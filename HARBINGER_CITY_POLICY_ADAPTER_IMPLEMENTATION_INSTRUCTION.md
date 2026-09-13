# CITY × Harbinger Policy Adapter — Implementation Instruction

## Objective

Make Harbinger’s raw graph useful to CITY without letting Harbinger decide CITY law.

Harbinger already consumes CITY’s frozen 13-file Phase 5 source manifest. Its first record is valid raw evidence:

```text
record: city.harbinger_source_effect_bridge.v1
verdict: raw_evidence_valid_incomplete
edges: 45
unclassified: 45
authority: none
```

The next slice maps each Harbinger edge to an exact CITY policy decision. It does not open acquisition, release, live Unreal execution, trusted CI, or a Phase 5 seal.

## Fixed Inputs

Use fresh inputs. Do not reuse `/private/tmp/city-harbinger-run` as authority.

| Input | Required relation |
|---|---|
| `proof_kernel/city_live_evidence_source_audit_contract.json` | Read it as the CITY source and effect law. Validate all 13 declared file hashes before use. |
| `proof_kernel/run_harbinger_city_source_effect_audit.py` | Keep its external-output rule and its false authority flags. |
| `../Harbinger/harbinger` | Run only the committed Harbinger core. Record its receipt, snapshot, graph, and candidate digests. |
| Fresh external output root | Must be empty, absolute, and outside CITY. |

The initial observed bridge record was bound to CITY commit `5d32a90139fb398e7bc4be619feff6e2b0de3f9f` and CITY frozen-contract SHA-256 `e1ce699b83a24cd6a7b47ac7d06b43f75e4f030879122e2d543b36ce7b4f2513`. A later run must report its own identity. It must not inherit this record’s authority.

## Deliverables

Add these CITY-owned files:

```text
proof_kernel/city_harbinger_policy_adapter.py
proof_kernel/city_harbinger_policy_contract.json
proof_kernel/verify_city_harbinger_policy_adapter.py
proof_kernel/test_city_harbinger_policy_adapter.py
```

The bridge may call the adapter after it receives Harbinger’s graph. Keep the adapter outside Harbinger. CITY owns this interpretation.

## Contract Shape

The policy contract must bind:

```text
schema
CITY frozen-contract SHA-256
Harbinger graph SHA-256
Harbinger source-snapshot SHA-256
Harbinger core identity or receipt SHA-256
exact edge decisions
required unmapped-edge behavior
authority = all false
```

Each decision must name all of these values:

```text
edge_id
graph family
source path
source line
source callable
Harbinger input or consequence token
CITY classification
CITY reason code
CITY contract rule or exact call-site reference
```

Use only these classifications:

```text
allowed
denied
unclassified
```

An `allowed` edge needs an exact CITY contract reference. A partial call name, a broad language allow-list, or a matching category is insufficient.

## Mapping Rules

1. Run a fresh bridge. Read the actual graph from its hash-bound packet.
2. Enumerate all 45 current Harbinger edge IDs. Do not rely on count alone.
3. Map an edge only when CITY’s frozen contract already proves its source, owner, line, and effect.
4. Preserve CITY’s distinctions:
   - filesystem and configuration identity reads are `provenance` only;
   - Unreal actor creation and destruction are `representation` only;
   - `admit_external_input_candidate` and `resolve_external_batch` are bounded canonical interfaces;
   - test-only controls remain test-only;
   - live `CasePrefixExecution._emit` is not a diagnostic edge;
   - dynamic receivers and inherited environment remain unresolved until their receiver or boundary is independently proved.
5. Any graph edge absent from the policy contract must be emitted as `unclassified` with `lcer.harbinger_edge_unmapped`.
6. Any graph, source snapshot, source file, contract, receipt, or policy mismatch must fail with `lcer.harbinger_policy_record_invalid`. Do not emit a candidate.
7. The adapter must write a canonical, digest-bound CITY record outside CITY’s source tree.

## Mandatory Negative Controls

Write argv-backed tests for each case:

```text
fresh valid bridge record                         -> raw valid, incomplete
one source byte changed                           -> reject before mapping
Harbinger graph SHA changed                       -> reject
snapshot SHA changed                              -> reject
receipt SHA or Harbinger identity changed         -> reject
one allowed edge moved to another line            -> reject
one unmapped edge marked allowed                  -> reject
one live self._emit edge marked diagnostic        -> reject
one dynamic resolve edge marked allowed           -> reject
one authority flag changed to true                -> reject
missing edge from the policy contract             -> unclassified, not dropped
```

Retain CITY’s existing fourteen frozen source adversaries. Harbinger’s generic graph does not replace their CITY detectors. The adapter must state that limit in its record.

## Required Output

Emit this shape:

```text
schema: city.harbinger_policy_adapter.v1
status: pass | fail
verdict: raw_evidence_valid_incomplete
source identity
CITY frozen-contract digest
Harbinger snapshot, graph, candidate, and receipt digests
mapped edge count
unclassified edge count
edge decisions
retained CITY adversary limit
authority:
  may_open_acquisition: false
  may_open_release: false
  may_seal_phase_5: false
record_sha256
```

`status: pass` only means the adapter correctly represented incomplete raw evidence. It never means Phase 5 passed.

## Validation

Run these commands from CITY:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest proof_kernel.test_city_harbinger_policy_adapter
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest proof_kernel.test_city_live_evidence_source_audit
python3 -B proof_kernel/run_harbinger_city_source_effect_audit.py \
  --root "$PWD" --harbinger-root ../Harbinger \
  --output /private/tmp/city-harbinger-policy-run --json
git diff --check
```

After an authorized commit, refresh the CITY mount and validate the exact committed native adapter through ControlTower.

## Stop Condition

Stop after the host adapter and independent validator pass their own tests and produce a fresh raw-incomplete record.

Do not change `lcer.acquisition_implementation_incomplete` or `lcer.release_semantics_not_implemented`. Do not launch Unreal. Do not claim a Phase 5 seal.
