# CITY Phoenix PR2 — Harbinger Source-Effect Closure

## Assignment

You are executing **PR2 Bootstrap Integration** in the active PhoenixRising
session:

```text
phoenix-mcdp-city-live-evidence-spec
```

The MCDP session `mcdp-city-live-evidence-spec` is complete through P16. Its
sealed handoff targets CITY. Phoenix is already mounted. PR1 is complete. PR2
is the current step.

Build a CITY-owned, independently verified **complete source-effect closure**
for the frozen Live Cross-Domain Evidence Round-Trip source scope. Use
Harbinger as the generic graph engine. CITY owns the scope, source meaning,
and acceptance decision.

This is a preflight gate. It does not run Unreal. It does not run a real build.
It does not acquire live evidence.

## Authority Boundary

Keep these values false in every new or changed record:

```yaml
may_open_acquisition: false
may_open_release: false
may_seal_phase_5: false
```

Keep these denials in place:

```text
lcer.acquisition_implementation_incomplete
lcer.release_semantics_not_implemented
```

A green result means only this:

```text
The frozen CITY source scope has an exact, complete, independently checked
source-effect model suitable to become an acquisition preflight input.
```

It does **not** mean Phase 5 is acquired, released, sealed, trusted, or ready
to launch.

## Read Before Editing

Read these files and validate their declared identities before changing code:

```text
AGENTS.md
PHASE_5_SELECTION.json
PHASE_5_FREEZE.json
docs/mcdp/live-evidence-contract/P14_DOCUMENTATION.md
docs/mcdp/live-evidence-contract/APPLICABILITY.md
docs/mcdp/live-evidence-contract/P16_SEAL_RECORD.md
proof_kernel/city_live_evidence_source_audit_contract.json
proof_kernel/run_harbinger_city_source_effect_audit.py
proof_kernel/city_harbinger_policy_adapter.py
proof_kernel/city_harbinger_policy_contract.json
proof_kernel/verify_city_harbinger_policy_adapter.py
proof_kernel/city_live_evidence_two_edge_closure_contract.json
proof_kernel/verify_city_live_evidence_two_edge_closure.py
HARBINGER_CITY_POLICY_ADAPTER_IMPLEMENTATION_INSTRUCTION.md
HARBINGER_CITY_TWO_EDGE_CLOSURE_CONTRACT_IMPLEMENTATION_INSTRUCTION.md
../Harbinger/AGENTS.md
../Harbinger/README.md
../Harbinger/harbinger
```

Use the exact public ControlTower route for Phoenix state. Do not create a
new MCDP or Phoenix session. Do not demount the active session.

```bash
./start.sh health --json
../ControlTower phoenix status phoenix-mcdp-city-live-evidence-spec --json
```

If the current worktree is dirty, preserve and report unrelated changes. Do
not reset them. If the declared frozen source identity does not match, stop.
Do not update hashes merely to make a changed source file pass.

## The Problem To Close

The existing bridge creates a valid raw graph for the frozen 13-file CITY
scope. It deliberately provides an empty Harbinger inventory policy and marks
the Harbinger adapter contract `scope_closure: partial`. That gives a valid
raw-incomplete record. It does not prove graph completeness.

The existing CITY policy adapter then interprets exact observed edges. That
adapter is valuable, but it is a second-stage CITY interpretation. It is not
proof that Harbinger's own input/effect model is closed.

The historical `145103` number is not a target. It is an old partial-analysis
observation. Never use it as a required count, a progress meter, or an
acceptance criterion.

The required result is a fresh Harbinger candidate whose closure is complete
for one exact frozen CITY scope and whose classifications are justified by
CITY-owned exact references.

## Fixed Scope

The source boundary is exactly the 13 entries declared by:

```text
proof_kernel/city_live_evidence_source_audit_contract.json
```

That contract contains four primary Python sources, seven plugin files, and
two discovered local Python imports. Treat every path, byte hash, and source
kind as an immutable input for this slice.

Rules:

1. Do not broaden the source scope by directory, glob, language, package, or
   nearby file.
2. Do not narrow it by dropping a file, an observed edge, or an unsupported
   construct.
3. A newly discovered import, include, generated dependency, external input,
   or effect is a failure until it is declared, bounded, and independently
   verified.
4. A changed source byte invalidates the run. It requires a new reviewed CITY
   source-audit contract. It may not inherit this result.
5. Harbinger must run from the committed `../Harbinger` checkout. Record its
   executable identity and validate its own receipt.

## Required Design

Add a separate CITY closure layer. Do not turn the existing raw bridge or the
policy adapter into an unreviewable multipurpose script. The exact filenames
may differ only when their purpose remains clear.

```text
proof_kernel/city_harbinger_source_effect_closure_contract.json
proof_kernel/city_harbinger_source_effect_closure.py
proof_kernel/verify_city_harbinger_source_effect_closure.py
proof_kernel/test_city_harbinger_source_effect_closure.py
```

The closure contract must bind:

```text
schema and contract digest
CITY commit and tree observed for the run
CITY frozen-source-audit contract digest
all 13 path, kind, and SHA-256 entries
Harbinger executable path and SHA-256
Harbinger source snapshot digest
Harbinger graph digest
Harbinger task receipt digest
the exact Harbinger inventory policy
the exact Harbinger adapter contract
every graph edge identity
every CITY classification reference
required external models
required effect models
required negative controls
false authority flags
closure-record digest
```

The constructor must write only to a new absolute output directory outside
CITY. Reject an existing output root, a symlinked path component, a path under
CITY, or a packet with unexpected files.

The independent verifier must not import the constructor or reuse its
classification decision functions. It must rebuild the expected relations
from the contract, source bytes, Harbinger artifacts, and raw graph.

## Exact Mapping Rule

Each classified Harbinger edge must have one CITY reference object containing:

```yaml
family: external_input_to_callable | function_to_consequence
path: repository-relative source path
line: exact positive source line
callable: exact qualified callable or native owner
token: exact observed input or callee token
classification: provenance | representation | canonical | test_control | build_execution
reference: exact CITY contract entry or named external/effect model
```

The tuple `(family, path, line, callable, token)` is the edge identity.
Category-only matching is forbidden. A matching token at another line is a
different edge. A matching callable with another token is a different edge.

Use CITY's existing meanings:

| Classification | Permitted meaning |
|---|---|
| `provenance` | Reads or observations used only to establish identity or inspect a process. |
| `representation` | Local Unreal or proof representation. Never canonical city mutation. |
| `canonical` | Only `admit_external_input_candidate` or `resolve_external_batch` at their declared CITY locations. |
| `test_control` | Test-only process or environment control. Never runtime authority. |
| `build_execution` | The sealed intercepted build boundary only. Never a successful build claim. |

Do not classify `self._emit`, unresolved dynamic receivers, arbitrary filesystem
access, inherited environment, arbitrary subprocess calls, generated code, or
unknown native calls by family alone. They remain failures until CITY supplies
an exact contract reference and the independent verifier proves it.

## Harbinger Model Requirements

Replace the bridge's empty inventory policy and `partial` adapter-contract
claim only through the new closure constructor.

The generated Harbinger policy must declare exact inputs, consequences, and
external models required by the current graph. It must be derived from the
CITY closure contract, not written as a loose second allow-list.

The generated Harbinger adapter contract must declare:

```yaml
adapter_id: city-live-evidence
scope_closure: complete
raw_graph:
  path: inventory/source-effect-graph.json
  sha256: <fresh digest>
```

Accept a Harbinger candidate only when all of these hold:

```text
candidate status is pass
candidate scope closure is complete
candidate failure_codes is empty
the graph has no unclassified edge
the graph edge set equals the CITY contract edge set
every classified edge has an exact CITY reference object
Harbinger receipt validation passes
the independent CITY verifier passes
all authority flags remain false
```

Do not treat a post-hoc policy-adapter mapping as a substitute for a complete
Harbinger candidate. Keep the adapter and its raw-incomplete record available
as a diagnostic cross-check. If its edge set disagrees with the closure graph,
fail the closure.

## PR2 Bootstrap Integration

Wire the closure as a required preflight input for the normal acquisition path.
The order must be visible in code and testable:

```text
authenticate frozen release and source identities
        ↓
construct and independently verify complete source-effect closure
        ↓
run all fourteen CITY frozen source adversaries
        ↓
only then reach the existing acquisition denial
        ↓
no build, launch, Unreal process, or canonical mutation
```

The normal release verifier must authenticate its own declared release before
importing adjacent mutable CITY code. Direct lower-level entrypoints must
enforce the same order. No command-line flag, environment setting, direct
Python import, root strategic tool, or test fixture may bypass it.

The result after a clean preflight remains the existing fail-closed denial:

```text
lcer.acquisition_implementation_incomplete
```

That is the positive control. A green source-effect closure is not permission
to remove it.

## Mandatory Negative Controls

Add argv-backed tests and independent-verifier cases for at least these
failures:

```text
one of the 13 source bytes changes                         -> reject
one declared source is missing, duplicated, or out of scope -> reject
new transitive local import or native include               -> reject
Harbinger executable byte or receipt changes                -> reject
snapshot, graph, task receipt, or candidate digest changes  -> reject
one graph edge is absent from the CITY closure contract      -> reject
one declared CITY edge is absent from the graph              -> reject
path, line, callable, family, or token changes              -> reject
classification has no exact CITY reference                  -> reject
category-only reference                                      -> reject
unknown external input or consequence                        -> reject
unresolved dynamic receiver or self._emit                    -> reject
Harbinger scope is partial                                   -> reject
Harbinger candidate has any failure code                     -> reject
Harbinger candidate has an unclassified edge                -> reject
one of the fourteen CITY adversaries fails                  -> reject before build
parent environment changes                                   -> same sealed preflight inputs
direct lower-level acquisition path                          -> same preflight and denial
release source changes before an adjacent import             -> reject before import
authority flag becomes true                                  -> reject
attempted compiler, Unreal, or process launch                -> test fails
existing or in-repository output root                        -> reject
tampered closure record                                      -> independent verifier rejects
```

Keep the existing two-edge closure tests. Keep the existing policy-adapter
tests. Add to them. Do not weaken them.

## Evidence and Validation

Run every command on a clean exact HEAD. Use a new external output root for
each complete run. Do not treat a receipt under `/private/tmp` as authority
for another commit.

At minimum, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  proof_kernel.test_city_harbinger_source_effect_closure
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  proof_kernel.test_city_harbinger_policy_adapter \
  proof_kernel.test_city_live_evidence_two_edge_closure \
  proof_kernel.test_city_live_evidence_source_audit
python3 -B proof_kernel/run_harbinger_city_source_effect_audit.py \
  --root "$PWD" --harbinger-root ../Harbinger \
  --output /private/tmp/city-harbinger-raw-cross-check --json
python3 -B proof_kernel/city_harbinger_source_effect_closure.py \
  --root "$PWD" --harbinger-root ../Harbinger \
  --output /private/tmp/city-harbinger-complete-closure --json
python3 -B proof_kernel/verify_city_harbinger_source_effect_closure.py \
  --root "$PWD" \
  --record /private/tmp/city-harbinger-complete-closure/city-harbinger-source-effect-closure-record.json \
  --json
git diff --check
./start.sh health --json
```

Before claiming success, commit the slice and repeat the complete suite at the
exact committed SHA. Then refresh and validate the CITY native adapter:

```bash
../ControlTower native refresh CITY --json
../ControlTower native validate CITY --expected-commit "$(git rev-parse HEAD)" --json
```

Record the exact commit, tree, command argv, output-root path, and result
digests in the PR2 checkpoint evidence. Use the existing active Phoenix
session. Do not complete PR2 until the full set is green.

## Stop Conditions

Stop and report `BLOCKED` if:

```text
the frozen source scope changes
Harbinger cannot express an exact required external model
an observed edge lacks an exact CITY reference
the complete candidate still reports a failure or unclassified edge
the source-effect closure would require a real build or Unreal launch
the normal acquisition or verifier path can bypass preflight
the phase contract would need to change
```

Do not fix a block by changing a count, accepting a broad category, hiding an
edge, moving the output into CITY, relaxing a denial, or updating a hash
without a reviewed source-contract transaction.

## Completion Claim

When every required test and independent verifier passes at exact committed
HEAD, report only:

```text
Phoenix PR2 source-effect preflight integration is proven as local development
evidence. CITY acquisition, release, trusted CI, live Unreal execution, and
Phase 5 seal authority remain closed.
```
