# Concurrent External Evidence Arbitration Proof Evidence

**Version:** 0.1.0
**Status:** Passed and sealed.
**Specification:** [Concurrent External Evidence Arbitration Proof — v0.1.0](Concurrent%20External%20Evidence%20Arbitration%20Proof%20-%20Draft.md)
**Payload schema:** `ConcurrentExternalEvidenceArbitrationPayload.v1`
**Simulation identity:** `0.7.0-draft.57`
**Scope:** Two isolated Unreal evidence sources, one exact R0-bound fixture
candidate set, one atomic external arbitration batch, one canonical successor,
and no live collection, networking, player topology, movement, streaming,
autonomous work, retries, randomness, or additional input classes.

## Verdict

> **Two independent Unreal domains can physically emit distinct valid evidence
> inputs against the same canonical source record, while one canonical batch
> alone orders and adjudicates those inputs into one deterministic successor
> independent of physical emission and harness-presentation order.**

The proof extends the sealed one-source lifecycle by exactly one dimension:

```text
one R0-bound physical evidence source
        ↓
two isolated R0-bound physical evidence sources
        ↓
one sealed fixture candidate set
        ↓
one R0-authorized external arbitration batch
        ↓
one private provisional evaluation
        ↓
one atomic canonical R1
```

It does not establish a collection window, timeout, live transport,
packet-order rule, retry, re-admission, or network arbitration law.

## Physical Unreal witnesses

W1–W4 used eight distinct UE 5.8 processes. Every process independently
verified the same raw R0 bytes and detached launch receipt, materialized its
own fixture-local surface, and emitted one exact Q only after an operator-
confirmed, source-audited first-person `E` interaction. Domain A and domain B
used distinct input, output, process, `UserDir`, and temporary roots; neither
was supplied or observed consuming the other domain's paths, and no shared
writable proof state was supplied. This is proof-domain/dataflow isolation,
not an OS sandbox claim.

| Witness | Physical emission order | Harness presentation order | Canonical member order | Canonical result |
| --- | --- | --- | --- | --- |
| W1 | QA, QB | QA, QB | QA, QB | `R1 = ad58d36d…` |
| W2 | QB, QA | QA, QB | QA, QB | `R1 = ad58d36d…` |
| W3 | QA, QB | QB, QA | QA, QB | `R1 = ad58d36d…` |
| W4 | QB, QA | QB, QA | QA, QB | `R1 = ad58d36d…` |

The verifier derives each observed physical order from exactly one timestamped
UE interaction line per process log and compares that result with the frozen
W1–W4 matrix. It does not trust harness capture-call order as the witness.

Each pair was concurrently alive before evidence capture. Both source
processes were terminated and their termination witnesses recorded before
the canonical BEXT resolver ran. Filesystem creation order, directory order,
process identity, PID, and presentation order remain non-authoritative trace.

The detached materialization and evidence-emission receipts bind each Q to the
exact accepted R0 bytes, canonical H0, physical actor, domain, input identity,
and physical-event identity. The release verifier byte-compares the captured
Q files with the frozen envelopes and cross-checks the receipts against the UE
logs and isolation audits.

## One atomic canonical batch

Both Q inputs are admitted side-effect-free against immutable R0. The sealed
fixture supplies the exact candidate set; it does not discover or collect it.
One BEXT capability is bound to H0 and derives member order only from:

```text
(occurrence_time, external_phase, canonical_external_priority, input_id)
```

The one canonical resolver produces this ordered adjudication:

```text
QA
  working P0: shared_slot owner = null
  ordinary gate: null == null → pass
  provisional mutation: owner = domain_A
  publication adjudication: mutation_committed

QB
  working PA: shared_slot owner = domain_A
  ordinary gate: domain_A == null → fail
  provisional mutation: none
  publication adjudication: failed_gate
  resource disposition: no_resource_acquired

close complete batch
  → publish one R1
```

QB is admitted and included in BEXT; it is not rejected or replayed merely
because its ordinary working-state gate fails. Both input and event identities
are adjudicated by the atomic batch, preventing either source from reacquiring
authority later.

The provisional P0/PA/PB identities use
`ExternalBatchWorkingStateIdentity.v1`, identity kind
`provisional_external_batch_working_state`, and a dedicated digest domain.
They are not canonical record hashes, cannot enter canonical record-identity
interfaces, cannot materialize, and cannot authorize later work. Only the
complete R1 crosses the singular publication point.

## Canonical identities and controls

```text
H0 = 668d86e3c96a99641d8d292fb2507bfd64b0edfadbe634fce5916fd45c3b0ce7
D0 = 8cea1aa6ae3ab2d7a25b6b660c91c26d26a1340ab4f2b67e134f7b7feb12cb12
H1 = ad58d36d44fb69aa5ac6e3e87a63657e0fc041f6c15cae280467fd7ba474adfd
```

All four W witnesses are byte-identical at R0 and R1, including singular
ancestry, one authoritative batch ledger, ordered member observations,
resource dispositions, adjudication barriers, and empty future schedule.

The singleton controls prove the shared-state law without a pair-specific
conflict rule:

```text
QA only → shared_slot = domain_A
QB only → shared_slot = domain_B
QA + QB → QA commits first by canonical key
          QB fails its unchanged ordinary availability gate
```

## Atomicity, replay, and source audit

The implementation records 47 fail-closed/order/fault witnesses. They cover:

- malformed, redirected, stale, replayed, or contract-incompatible Q;
- duplicate input/event identities and incomplete or altered fixture sets;
- caller-, UE-, filesystem-, process-, or metadata-owned ordering attempts;
- provisional/canonical identity substitution and provisional-state exposure;
- member-owned publication or mutation outside the declared contract; and
- six atomic fault points: after QA provisional mutation, after QB gate
  evaluation, during replay-barrier construction, during ledger construction,
  after complete R1 construction but before validation, and after validation
  but before publication.

Every structural or injected execution fault leaves canonical R0 byte-
identical, publishes neither a successor nor an adjudication barrier, and
preserves the private working state as disposable computation.

The mechanical source audit confirms:

```text
canonical resolver functions: 1
resolver publication returns: 1
policy / UE / process / presentation input to resolver: none
filesystem metadata reaches canonical ordering: false
live collection or timeout behavior: false
networking: false
randomness: false
member-owned successor publication: false
provisional identity accepted as canonical: false
```

## Verification record

- Full Python regression: **177/177** checks passed.
- Focused concurrent-arbitration suite: **16/16** checks passed.
- UE 5.8 `CityMaterializationProofEditor` build: **passed**.
- Physical source verification: **4/4 witness pairs; 8/8 distinct UE
  processes with disjoint audited proof roots**.
- Canonical regenerated artifact contract: **24/24** artifacts.
- Imported physical witness contract: **60/60** artifacts.
- Self-excluding release manifest: **111/111** artifacts.

The release verifier regenerates all canonical artifacts from the frozen
resolver and validates the imported UE artifacts without synthesizing Q or a
receipt.

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/verify_concurrent_external_evidence_arbitration_release.py verify
```

## Boundary

This proves exactly one two-member R0-bound external arbitration batch and one
atomic successor. It does not prove live input collection, transport
completeness, latency behavior, networking, 2+2 player topology, split crews,
movement, proximity, streaming, World Partition, autonomous batch members,
same-clock successor work in this fixture, retry, re-admission, randomness,
additional input classes, generalized arbitration, city scale, or production
performance. No successor scope follows from this seal.
