# CITY Phoenix PR2 — Harbinger v3 Successor Execution Order

## Status

This instruction supersedes the Harbinger-core block in:

```text
CITY_PHOENIX_PR2_HARBINGER_SOURCE_EFFECT_CLOSURE_INSTRUCTION.md
```

The active Phoenix session remains:

```text
phoenix-mcdp-city-live-evidence-spec
```

Current Phoenix step:

```text
PR2 — Bootstrap Integration
```

Harbinger now has the required committed core successor:

```text
repository: ../Harbinger
commit: 06fd396241fa28951003548110be87a386732c7a
title: Add hash-bound complete source-effect scope policy
```

That checkout has no configured Git remote. Use its local committed bytes. Do
not copy or vendor Harbinger code into CITY. Do not modify Harbinger during
this CITY slice.

## Result Required

Produce one fresh, CITY-owned, independently verified record proving that
Harbinger itself emitted a **complete** candidate for the exact frozen CITY
13-file source manifest.

```text
Harbinger v3 exact inventory policy
        ↓
Harbinger graph scope_status = complete
        ↓
Harbinger audit candidate status = pass
        ↓
CITY independently verifies every relation
        ↓
existing acquisition denial remains closed
```

This is PR2 preflight evidence. It does not authorize a build, Unreal launch,
live evidence acquisition, release, trusted CI, Phase 5 seal, or canonical
mutation.

Keep all authority flags false:

```yaml
may_open_acquisition: false
may_open_release: false
may_seal_phase_5: false
```

Keep both denials unchanged:

```text
lcer.acquisition_implementation_incomplete
lcer.release_semantics_not_implemented
```

## Execution Order

Perform these steps in order. Stop at the first failed gate. Do not substitute
a later result for an earlier one.

### 1. Establish the clean input set

Read and verify:

```text
AGENTS.md
PHASE_5_SELECTION.json
PHASE_5_FREEZE.json
proof_kernel/city_live_evidence_source_audit_contract.json
proof_kernel/city_harbinger_policy_contract.json
proof_kernel/run_harbinger_city_source_effect_audit.py
proof_kernel/city_harbinger_policy_adapter.py
proof_kernel/verify_city_harbinger_policy_adapter.py
proof_kernel/city_live_evidence_two_edge_closure_contract.json
CITY_PHOENIX_PR2_HARBINGER_SOURCE_EFFECT_CLOSURE_INSTRUCTION.md
../Harbinger/AGENTS.md
../Harbinger/docs/SOURCE_EFFECT_AUDIT_CONTRACT.md
../Harbinger/tools/harbinger_core.py
```

Verify all of these before code changes:

```bash
git -C ../Harbinger rev-parse HEAD
git -C ../Harbinger status --short
git -C ../Harbinger diff --check
git status --short
./start.sh health --json
```

Required conditions:

```text
Harbinger HEAD equals 06fd396241fa28951003548110be87a386732c7a
Harbinger worktree is clean
CITY worktree has no unrelated changes
CITY health status is pass
the CITY source-audit contract still declares exactly 13 source entries
```

If Harbinger is not at that exact commit, stop. Do not use a branch name, an
uncommitted local edit, or a copied executable as its identity.

### 2. Capture the current raw graph as a cross-check

Use a fresh external output root. The raw bridge stays intentionally partial.
It proves the exact graph CITY must model. It does not prove completion.

```bash
raw_root="$(mktemp -d /private/tmp/city-harbinger-v3-raw.XXXXXX)/run"
python3 -B proof_kernel/run_harbinger_city_source_effect_audit.py \
  --root "$PWD" --harbinger-root ../Harbinger \
  --output "$raw_root" --json
```

Record the packet paths and digests for:

```text
source snapshot
source-effect graph
Harbinger inventory receipt
Harbinger task-preflight receipt
raw audit candidate
raw audit receipt
```

Require these raw observations:

```text
scope_status: partial
edge_count: 45
unclassified_count: 45
failure_codes include harbinger.scope_incomplete
authority remains false
```

The count is an exact observed current graph relation, not a broad progress
metric. The historical `145103` value remains irrelevant.

### 3. Derive the v3 policy from CITY law

Add a separate CITY constructor and contract. Do not hand-write a loose
Harbinger policy inside the bridge.

```text
proof_kernel/city_harbinger_v3_closure_contract.json
proof_kernel/city_harbinger_v3_closure.py
proof_kernel/verify_city_harbinger_v3_closure.py
proof_kernel/test_city_harbinger_v3_closure.py
```

The constructor must derive `harbinger.inventory_policy.v3` from:

```text
the current frozen CITY source-audit contract
the exact raw graph captured in step 2
the existing 45 CITY policy mappings
the committed Harbinger core identity
```

The generated v3 policy must contain only these top-level fields:

```yaml
schema: harbinger.inventory_policy.v3
scope:
  source_snapshot_sha256: exact step-2 snapshot digest
  parser_configuration_sha256: exact Harbinger parser digest
external_models: exact model entries
edge_decisions: exact decision entries
```

Each edge decision must include:

```yaml
family: external_input_to_callable | function_to_consequence
path: exact repository-relative path
line: exact line
from:
  kind: external_input | callable
  id: exact Harbinger graph identifier
to:
  kind: callable | consequence
  id: exact Harbinger graph identifier
classification: allowed
model_id: exact declared model
```

For every v3 decision, the CITY closure contract must additionally bind an
exact CITY reference:

```yaml
classification: provenance | representation | canonical | test_control | build_execution
reference:
  path: source-audit contract path
  line: exact source line
  callable: exact CITY callable
  family: exact Harbinger edge family
  token: exact Harbinger input or consequence token
```

Use the existing `city_harbinger_policy_contract.json` mappings where they
match exactly. Do not change a source line, callable, family, or token to make
a mapping fit.

No v3 decision may be generated if its raw graph edge lacks one exact CITY
reference. That is a block. Do not add a category-wide model or a fallback
allow-list.

### 4. Bind models and edge set before invoking Harbinger

The constructor must validate these relations before `../Harbinger/harbinger`
is called:

```text
all 13 CITY source bytes match the frozen contract
Harbinger executable SHA-256 matches commit 06fd396
Harbinger parser configuration matches the v3 scope field
the raw graph is authenticated by its receipt
the raw graph has exactly the declared CITY edge set
each of the 45 edges has one and only one exact CITY reference
every external input and consequence has an exact v3 external model
the v3 policy edge set equals the raw graph edge set
the new output root is absolute, fresh, external to CITY, and symlink-free
```

Model semantics stay narrow:

```text
os.environ / sys.argv         -> test-control input models only
subprocess.run / Popen        -> exact test-control, provenance, or intercepted build models
canonical interfaces          -> only the declared CITY arbitration references
Unreal representation         -> representation only
```

No model grants authority. A model identifies a source-effect relation.

### 5. Invoke Harbinger v3 in a fresh packet

Run a new source snapshot and task preflight. Then run inventory with the
generated v3 policy. The v3 graph must be the graph used by the candidate.

```bash
complete_root="$(mktemp -d /private/tmp/city-harbinger-v3-complete.XXXXXX)/run"
python3 -B proof_kernel/city_harbinger_v3_closure.py \
  --root "$PWD" --harbinger-root ../Harbinger \
  --output "$complete_root" --json
```

The constructor must run these Harbinger commands with argv lists, not shells:

```text
harbinger snapshot create
harbinger task preflight
harbinger inventory --policy <generated-v3-policy>
harbinger audit --contract <complete-adapter-contract>
harbinger receipt validate
```

The adapter contract must bind the fresh graph digest and say:

```yaml
schema: harbinger.adapter_contract.v2
adapter_id: city-live-evidence
scope_closure: complete
raw_graph:
  path: inventory/source-effect-graph.json
  sha256: exact fresh graph digest
```

### 6. Verify the complete Harbinger result

Accept the candidate only if every condition is true:

```text
inventory graph scope_policy_version == 3
inventory graph scope_status == complete
inventory graph scope_failure_codes == []
edge_count == expected_edge_count == 45
edge_identity_sets_match == true
unclassified_count == 0
denied_count == 0
Harbinger candidate status == pass
Harbinger candidate failure_codes == []
Harbinger receipt validation == pass
```

Then run the independent CITY verifier:

```bash
python3 -B proof_kernel/verify_city_harbinger_v3_closure.py \
  --root "$PWD" \
  --record "$complete_root/city-harbinger-v3-closure-record.json" \
  --json
```

The verifier must recompute source hashes, Harbinger identity, parser digest,
v3 policy decisions, graph identity set, external-model references, candidate
identity, receipt identities, and all false authority flags. It must not
import the constructor or reuse its classification function.

### 7. Integrate the PR2 preflight without opening the gate

Only after the independent verifier passes, wire the closure into the normal
acquisition and release-verification entrypoints in this order:

```text
authenticate exact release/source identity
        ↓
verify complete Harbinger v3 closure
        ↓
run the fourteen frozen CITY source adversaries
        ↓
return lcer.acquisition_implementation_incomplete
        ↓
never reach build, launch, Unreal, or canonical mutation
```

The same order must hold for direct lower-level paths. No opt-in flag,
environment variable, direct import, test fixture, or root route may skip it.

The positive test is a clean preflight that still returns:

```text
lcer.acquisition_implementation_incomplete
```

Do not alter `lcer.release_semantics_not_implemented`.

### 8. Run adversarial tests

Add argv-backed tests for each case:

```text
Harbinger commit or executable byte changes                 -> reject
one frozen CITY source byte changes                         -> reject
parser identity changes                                     -> reject
raw graph, snapshot, candidate, or receipt changes          -> reject
one of 45 raw edges is absent                                -> reject
one declared v3 edge is not observed                        -> reject
path, line, caller, family, or token changes                -> reject
model token or model kind does not match endpoint            -> reject
v3 graph stays partial                                      -> reject
candidate has a failure code                                -> reject
any unclassified or denied edge                             -> reject
one CITY reference is absent or category-only               -> reject
one of fourteen CITY adversaries fails                      -> reject before build
parent environment changes                                  -> identical sealed preflight inputs
direct acquisition route                                    -> same preflight then existing denial
mutable release source before adjacent import               -> reject before import
authority flag true                                         -> reject
attempted compiler, Unreal process, or launch               -> fail test
existing, symlinked, or in-CITY output root                 -> reject
tampered closure record                                     -> independent verifier rejects
```

Retain all existing City policy-adapter, source-audit, and two-edge closure
tests. Do not weaken or delete a negative control.

### 9. Commit, repeat, and checkpoint

Before the commit, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  proof_kernel.test_city_harbinger_v3_closure \
  proof_kernel.test_city_harbinger_policy_adapter \
  proof_kernel.test_city_live_evidence_two_edge_closure \
  proof_kernel.test_city_live_evidence_source_audit
git diff --check
./start.sh health --json
```

Commit only the reviewed CITY transaction. At the exact committed HEAD, rerun
the full suite and both fresh external-output workflows. Then run:

```bash
../ControlTower native refresh CITY --json
../ControlTower native validate CITY --expected-commit "$(git rev-parse HEAD)" --json
```

Attach the exact commit, tree, v3 policy digest, graph digest, candidate
digest, receipt digest, CITY closure-record digest, and command argv to the
active Phoenix PR2 checkpoint evidence.

## Stop Conditions

Stop and report `BLOCKED` if any of these occur:

```text
Harbinger is not exactly at 06fd396
the 13-file CITY scope changes
the raw graph is not exactly covered by CITY mappings
an external model cannot be exact
Harbinger v3 emits partial, a denial, or an unclassified edge
the closure requires a real build or Unreal launch
the normal acquisition path can bypass preflight
the work would change an acquisition, release, or Phase 5 authority flag
```

Never resolve a block by relabelling raw evidence, using the old `145103`
count, broadening a model, dropping an edge, copying Harbinger into CITY,
changing a hash without a source-contract review, or relaxing a denial.

## Allowed Completion Claim

After all post-commit checks pass, report only:

```text
Phoenix PR2 now has a CITY-owned, independently verified Harbinger v3 complete
source-effect preflight for the frozen 13-file scope. Acquisition, release,
trusted CI, live Unreal execution, and Phase 5 seal authority remain closed.
```
