# Live Cross-Domain Evidence Round-Trip Proof

**Version:** 0.1.0-draft.2
**Status:** Operator-selected Phase-5 specification-review candidate. Unfrozen.
**Implementation authority:** None until exact specification review and freeze.
**Evidence:** Not acquired. No new proof seal. Capacity remains v0.1.11.

## Decision and authority

On 2026-09-06 the operator approved the proposed successor with “Approved. Execute”. The selection is: two original live Unreal domains emit competing evidence, one canonical batch commits, and both original domains display its result without restarting.

This document and `proof_kernel/live_cross_domain_evidence_round_trip_contract.json` form one review candidate. `PHASE_5_SELECTION.json` binds their bytes and supplies current development routing. It supersedes historical “no successor selected” routing only. The Phase-4 seal, continuation 0.7.0-draft.83 and capacity v0.1.11 retain their historical claims and bytes.

The root closure for this change covers the selection, document validator and native status wiring. It does not freeze this game specification. Structural document validation is not independent semantic acceptance, a live run or a game seal.

## Question and acceptance

Can the same two Unreal processes remain alive from initial representation, through their two physical proposals and one canonical commit, until both represent the settled result?

Use the exact sealed concurrent-arbitration fixture. Both domains request `shared_slot_01`. The existing canonical key orders QA before QB. QA acquires the available resource. QB fails its unchanged ordinary availability gate. One R1 records both adjudications. Every successful witness produces the exact sealed R0 and R1 bytes.

Test all eight combinations of physical emission order, harness presentation order and post-commit refresh order. The JSON contract enumerates W1–W8. This is a fixed, complete two-member set. It is not a live collection or timeout policy.

## Why a separate proof is needed

The existing arbitration harness requires source termination before candidate-set validation and resolution. Its Unreal adapter only accepts frozen R0. Phase 4 retains and refreshes two original live domains, but admits no physical input into its canonical transition. Those separate results do not establish this round trip.

The candidate changes the physical lifecycle around the existing arbitration law. It does not revise the canonical payload, Q schema, key, gate, resolver, replay identities or result. All named predecessor documents, canonical files and implementation sources are pinned in the JSON contract.

## Ownership

| Surface | Owner | Allowed consequence |
| --- | --- | --- |
| Canonical R0, R1, ordering, gates, ancestry and adjudications | Existing Python arbitration functions | One validated, atomic successor |
| Physical interaction and Q emission | Domain-local Unreal Actor | Non-authoritative proposal |
| Complete fixed-set admission | Python harness and existing admission functions | One R0-bound batch capability |
| Provisional member working state | Existing resolver | Private computation only |
| Current canonical head | Python harness | Select committed projection after resolution |
| Refresh and Actor state | Each original Unreal domain | Disposable representation |
| Receipt | Emitting component | Provenance requiring independent checks |
| Live observation | Separate world-enumeration probe | Observed representation, no canonical authority |
| Final witness acceptance | Independent release verifier | Bounded development result |

No peer-domain callback, physical timing, PID, wall clock, pipe order, guard state or receipt may select canonical order or mutate canonical state. The representation guard is a harness claim gate. It is not a prerequisite input to the canonical resolver.

## Canonical inputs and byte boundaries

The JSON contract pins four stored predecessor artifacts: R0, R1, QA and QB. It also pins the original arbitration implementation and both predecessor specifications/evidence records.

Import `initial_canonical_envelope`, `admit_external_input_candidate`, `primary_fixture`, `construct_bext_from_sealed_fixture_set` and `resolve_external_batch` from the sealed arbitration module. Read captured Q bytes from the real source outputs. Never synthesize Q and call it a physical emission.

Retain the predecessor canonical serialization and hash laws. QA/QB envelopes and detached predecessor acceptance/emission receipt shapes stay exact. Additional lifecycle provenance uses a separate wrapper, never extra fields inside a frozen Q or canonical payload.

For all new detached JSON messages: UTF-8; one JSON object; duplicate keys rejected at every nesting level; non-finite numbers rejected; unknown, missing and extra fields rejected. Canonical storage uses sorted keys, compact separators, ASCII escapes and one trailing newline. Raw SHA-256 hashes the stored bytes including that newline. The wrapper hashes bytes; it does not replace the predecessor canonical digest.

An operation wrapper binds schema, witness, domain, launch, operation and binding digest. A materialize command carries the exact immutable committed record bytes plus a projection. Initial R0 also carries the exact predecessor launch receipt. `record_delivery` defines their authentication order. No child file reader supplies these bytes. Process binding grants no canonical authority.

## Process identity and isolation

Launch exactly two direct children per ordinary witness. Their process roots are fresh, absolute, disjoint directories under one fresh private temporary root. Reject symlinks and reused output directories. The full original process identity remains fixed through L0–L5.

Bind every field listed in `process_binding_fields`: witness and domain; unique launch identity; PID and macOS birth tuple; executable and project real paths/hashes; complete loaded proof-module inventory hash; argv/environment/descriptor hashes; and process root. Hashes are observed by the parent. Child-supplied identity fields must match them.

Record parent wait/poll state, birth identity and pipe continuity at each checkpoint. A copied label or a new process with the old PID claim cannot substitute for the original. No child may receive the other domain's paths or a writable canonical output path. Parent/child pipes carry only declared commands and responses. Other inherited proof descriptors are forbidden. This is proof dataflow isolation, not an OS sandbox claim.

## Ordered lifecycle

| Checkpoint | Canonical state | Required physical state |
| --- | --- | --- |
| L0 | R0 | Both original domains display the available resource and pass live census. |
| L1 | R0 | QA and QB were physically emitted in the witness order. Both processes remain alive. |
| L2 | R0 | Both exact inputs are admitted side-effect-free. The complete fixed set forms one batch. |
| L3 | R1 | One canonical commit occurred. Both original R0 representations are stale. |
| L4 | R1 | First refreshed domain displays R1. Its peer remains stale R0. |
| L5 | R1 | Both original domains display the same committed owner and pass live census. |

Keep both source processes alive during admission and resolution. Sample liveness immediately before and after the canonical call. Canonical execution still receives only the existing immutable record and declared batch arguments. A physical failure detected after publication cannot undo the result.

Disable claims of current representation before committing. Commit through the existing resolver once. Bind the published head to exact R1 bytes. Refresh in the witness order. For each refresh, disable the local claim, destroy all old proof-generation Actors, verify their absence, create the new resource Actor, and publish its head anchor last. Only an exact independent live census may enable a current-head claim.

After L5 and surviving evidence capture, terminate the original children and record their exit. Termination is cleanup, never a prerequisite for canonical resolution in this successor.

## Physical emission

Each domain has one bound interaction Actor. A declared parent command triggers its local Unreal interaction once. The Actor derives the exact allowed proposed consequence from its accepted R0 and domain contract. It emits the existing Q plus the existing detached emission receipt and a new lifecycle wrapper.

The wrapper records the strictly increasing physical interaction counter, physical event ID, source-record hash and exact Q hashes. The harness compares it to an independently captured process log event. Physical emission order comes from those events. Presentation order is recorded separately. An echo of a command or a harness-generated Q is not evidence of Actor execution.

This fixture does not introduce a player pawn, keyboard input, network packet collection, streaming input or late-input policy.

## Committed projection and live oracle

The projection accompanies exact committed arbitration record bytes. It contains the domain, generation, record identity and owner needed to represent R0 or R1. The child computes hashes from received bytes. R0 uses the preserved launch/acceptance rules. R1 uses the separately closed representation receipt. Reject provisional bytes, stale R0 refresh, wrong domain, altered binding and an owner inconsistent with the authenticated bytes.

Use one head-anchor Actor and one resource-state Actor per domain. R0 shows owner null; R1 shows domain_A. Both Actors expose their immutable generation, bound record and semantic role for independent enumeration. No second owner or old proof-generation Actor may coexist with an accepted current representation.

The live probe enumerates the actual UWorld proof Actors. It consumes neither expected projection JSON nor materialization receipt. The parent independently derives the expectation from pinned canonical bytes. Compare exact cardinalities, roles, record, generation and owner. The receipt, live observation and independently derived expectation must all agree.

The closed observation retains every world context and raw Actor row. Each proof Actor has its own role, domain, record hash, generation and owner. `world_oracle` fixes world selection, exhaustive level-array traversal, Actor identity and the relevant-Actor predicate. The verifier derives counts and ownership from rows. It rejects wrong-world, mixed-generation, incomplete and pending-destruction censuses. Aggregate fields must match those calculations.

## Failure contract

The JSON contract retains eighteen F-families. `failure_programs` enumerates twenty-one executable runs. F04, F10 and F16 each have two distinct subcases. Every run fixes its command prefix, executor, domain, stage, exact mutation, invocation, underlying code and terminal world. `failure_execution_law` fixes actual-call and raw-evidence assertions. A normalized LCER code alone cannot satisfy a run.

F01–F09 operate on fresh pre-commit pairs. An incomplete, malformed, redirected, duplicated, stale or incompatible input cannot publish R1. Process replacement/exit and attempted provisional projection also fail that witness. Measure R0 bytes before and after each rejected attempt.

F10–F18 first establish one valid commit. Replayed input cannot create another successor. Loss of either domain, partial refresh, false receipts, wrong live owner, old-generation Actors, stale projection and altered binding cannot rewrite R1 or claim synchronized representation. After a terminal failure, stop the witness. Do not retry, re-admit, restart or repair a domain inside it.

Also execute the six named real fault hooks in the existing canonical resolver, each with a fresh pair and valid captured inputs. Every injected fault leaves R0 byte-identical and produces no published successor or replay barrier. Record fault-hook invocation and outcome rather than describing a synthetic result as execution.

Failure before complete-set admission may abort the witness. Once the complete valid batch has committed, display failures affect only representation. A timeout is a terminal observation/acquisition failure. It cannot remove a candidate, select a winner, advance the canonical clock or manufacture a receipt.

## Additive Unreal integration candidate

Preserve the original Unreal module and its sealed source bytes. The candidate uses an additive runtime plugin inside the existing `CityMaterializationProof` project. Its module is `CityLiveEvidenceProof`; its URL-selected game mode is `/Script/CityLiveEvidenceProof.CityLiveEvidenceGameMode`. It owns the bounded command loop, interaction Actor, head/resource Actors and independent world probe.

Use the existing UE 5.8 editor and project at Projects/CITY. The launch tuple is: editor executable; absolute CITY project; `/Engine/Maps/Entry?game=/Script/CityLiveEvidenceProof.CityLiveEvidenceGameMode`; `-game`; `-unattended`; `-nosplash`; `-NoSound`; `-log`; and declared domain/binding/root arguments. The JSON contract fixes the complete launch argv, seven-variable environment, cwd, inherited descriptor identities, startup handshake, command grammar, operation IDs and closed wire schemas. `process_input_contract` also closes config, loaded-image and source-dataflow acceptance. Actual GameMode identity and initial Actor census must pass before binding. All other proof-semantic launch settings are rejected.

The additive plugin path is a proposed way to respect original-file preservation. Discovery, compilation and exact game-mode dispatch remain untested. A reviewer must reject this integration choice if it needs undeclared edits to sealed files or hidden engine input. Do not silently broaden the allowed paths to make it build.

## Planned source, CLI and release surface

`planned_source_paths` is the complete proposed source set. The existing canonical module stays unchanged. The new harness, model, verifier and tests live in `proof_kernel`; the new Unreal module lives only under the named plugin path. There is no existing successor acquisition command yet.

The JSON contract records planned acquire, verify and unittest argv. Brace values are typed caller arguments, not shell expansion. Runtime parent must be an absolute fresh private directory. Acquisition output must be a new directory. Verification is read-only, rejects symlink members and writes any derived comparisons outside the source release.

A witness contains every field in `output_fields`. Successful and failed runs retain launch plans, exact executed argv/environment/descriptor inventories, process identities, raw commands/responses, real Q bytes, detached receipts, live observations, canonical artifacts, explicit dispositions and a hash-bound artifact index. Logs are append-only per run. A final top-level acquisition record enumerates all expected witnesses and files and records build/executable/project identity.

The independent verifier must derive canonical results with the predecessor functions, verify captured Q against physical emissions, reconstruct every lifecycle and failure disposition from raw records, compare all eight canonical results byte-for-byte, and reject missing/extra/altered evidence. It may not trust harness success booleans or count labels as its oracle.

The final manifest enumerates exactly 289 members and excludes itself. The release contains 219 artifact files, all proposed game sources, both spec files and the unchanged executable dependencies. `kernel.py` and all original project/config/source build inputs are hash-bound. The document checker stays outside this game release. `artifact_hash_graph` fixes every index target and construction order. Acquisition lists itself as a filename but hashes only the other 218 artifacts. The final manifest hashes acquisition. Each case index hashes only its own closed streams and trace. These are candidate requirements; no release exists yet.

## Acquisition cost

Budget one successful UE build for each candidate source identity. One complete proposed acquisition has eight primary pair runs, twenty-one failure pair runs and six canonical-fault pair runs: thirty-five pairs, seventy original launches and one replacement-process adversary. Offline verifier mutations add no UE processes. Each case has a 900-second outer limit and each blocking protocol operation a 60-second timeout. Actual wall time is unmeasured.

The implementation freeze must include the exact fault injection command surface and cost. Reacquire after a source identity changes; never reuse an older binary receipt as proof of new source. CITY's live execution remains unverified until a real run names the CITY project and loaded modules.

## Review and freeze checklist

The independent reviewer must decide whether:

1. Canonical law is reused without changing frozen inputs or semantics.
2. Every successful witness retains the same two live source processes through commit and result observation.
3. New wrappers, process input closure and byte rules are complete and closed.
4. The live oracle is independent of receipts and expected payloads.
5. Every negative has a real allowed trigger and an exact assertion over raw evidence.
6. Plugin discovery and game-mode selection are explicit and compatible with original-file preservation.
7. Exact command/environment/descriptor fields, artifact filenames and full release membership are complete enough to freeze.
8. The priced acquisition matrix matches every required control and the claimed boundary.

The JSON contract supplies the byte schemas, launch inputs, failure matrix, exact path set and release enumeration for this review. The additive plugin integration is a design candidate whose runtime feasibility must be demonstrated during authorized implementation. Independent review must assess completeness and reject any unsupported acceptance claim. A document checker cannot accept the design on the reviewer’s behalf.

After corrections, bind the full candidate to its Git commit/tree and an independent review verdict. Only then record a specification freeze and a clean implementation contract. Continue the actual MCDP session without inventing completed phases. PhoenixRising may start only from its emitted P16 handoff. Implementation and acquisition follow that accepted authority; game sealing requires separate exact-result review.

## Draft 2 correction boundary

Independent review of draft 1 at `e8425b00285ba34d1cc034d4e983955ee57915e1` returned **REVISE**. This candidate addresses R1–R7. It has not received independent acceptance.

| Finding | Normative contract section | Required result |
| --- | --- | --- |
| R1. Raw R0 acceptance | `record_delivery`, `materialize_input` | Authenticate actual bytes before the preserved acceptance receipt and physical emission. R1 has distinct representation semantics. |
| R2. Evidence closure | `wire_schemas`, `schema_contract`, `verifier_negative_cases` | Close every new response, receipt, lifecycle, trace and artifact object. Match command/response and raw-byte relations. |
| R3. Actor oracle | `world_oracle`, `world_row`, `actor_row` | Keep raw per-Actor facts. Derive accepted cardinality, generation and owner independently. |
| R4. Executable failures | `operation_schedule`, `failure_programs`, `failure_execution_law` | Execute exact mutations at real boundaries. Retain before/after bytes, consumed hooks and terminal physical facts. |
| R5. Process inputs | `process_input_contract`, `startup`, `process_observation` | Check actual GameMode, worlds, inputs, descriptors and original process identity. Reject undeclared semantic input edges. |
| R6. Dependencies | `unchanged_dependencies`, `dependency_contract` | Authenticate canonical serializer and complete local executable/build dependencies before use. Record external engine/toolchain inputs under the closed acquisition procedure. |
| R7. Hash graph | `artifact_hash_graph` | Build a directed acyclic index. No file supplies its own raw hash. |

The forty-one JSON schema definitions form one local draft-2020-12 `$defs` bundle. Every object has an exact required field set and forbids extra fields. Schema validity and the cross-record relations in `schema_contract` both apply. The raw predecessor records and receipts retain their exact existing schema and byte validation; embedding them as UTF-8 strings does not relax their contract.

Partial refresh is explicit. F13/F14 fail after the R1 resource exists and before its anchor is published. That domain is unavailable. Its old R0 Actors are gone. Its surviving peer remains stale R0. Neither canonical rollback nor an intact predecessor representation is claimed. A terminal read-only census captures the partial world; it cannot repair it.

All positive and failure runs use the recursive command prefixes in `operation_schedule`. Fault hooks never select a canonical consequence. Only the five declared child-owned fault runs may arm Unreal. Harness-owned mutations preserve the original physical captures and retain altered copies separately as actual rejection arguments. The six existing resolver fault hooks remain unchanged.

The review-only checker validates schema definitions and structural adversaries. Its local Python environment requires `jsonschema`. That dependency is outside the proposed game release, along with the checker and CITY native selection code. Passing it proves no source-dataflow audit, Unreal build, physical fault, acquired release or independent acceptance.

## Current executable checks

```sh
cd /Users/boandersson/Projects/CITY
python3 -B proof_kernel/validate_live_cross_domain_evidence_round_trip_spec.py --json
python3 -B proof_kernel/validate_live_cross_domain_evidence_round_trip_spec.py --self-test --json
./start.sh strategic-status --json
./start.sh next-action --json
```

These check document integrity, closed structural commitments, selected-state routing and negative document mutations. They do not compile Unreal, acquire evidence, provide independent specification acceptance or authorize a game seal.
