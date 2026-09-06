# CITY draft-3 focused independent review

**CONTRACT_CONFORMANCE — CONTINUE.** No remaining findings in this focused review. Draft 3 is ready for an operator specification-freeze decision. This advice does not freeze the specification or authorize implementation or a game seal.

Exact candidate: commit `712fff25e3e256a77b733f7ca108aa9d7ad00d1e`, tree `7000cda24b090f2b1fd34b41b7cb524034590071`. Reviewed the diff from `1ea8c897dad549ba62c8be9b0fdbcca09a837c67`. CITY remained clean and the reviewed bytes stayed fixed.

Start: 2026-09-06T20:09:54.349513+00:00. Finish: 2026-09-06T20:12:35.633383+00:00. Branch: main. Cached upstream at start: 1	0; at finish: 1	0. Any transport-only change is recorded separately from source identity.

**R2 is closed.** The old opaque argument and fault-state fields are removed. Three closed argument schemas bind each canonical function. `call_trace_contract` fixes positional/keyword reconstruction, exact nested predecessor objects and the finite failure deviations, returned-value encoding, canonical base64 and mandatory typed before/after snapshots. A valid parsed Q stays separate from its actual raw bytes, preserving the F02 missing-LF case. F10b retains its declared digest mismatch and still reaches the original event replay barrier.

Evidence: [live_cross_domain_evidence_round_trip_contract.json:2957](</Users/boandersson/Projects/CITY/proof_kernel/live_cross_domain_evidence_round_trip_contract.json:2957>), [call trace rules](</Users/boandersson/Projects/CITY/proof_kernel/live_cross_domain_evidence_round_trip_contract.json:4752>).

**R4 is closed.** `canonical_fault_codes` contains the six complete hook-specific rejection strings. Each matches the real exception retained by this reviewer in the prior offline probe. The revised C01–C06 program requires the full matching code and rejects the unsuffixed family label. The resolver source remains unchanged.

Evidence: [C programs](</Users/boandersson/Projects/CITY/proof_kernel/live_cross_domain_evidence_round_trip_contract.json:4108>), [exact codes](</Users/boandersson/Projects/CITY/proof_kernel/live_cross_domain_evidence_round_trip_contract.json:4780>), [comparison](</private/tmp/city-independent-review-7yjg2eg3/focused-comparison.json>).

**Prior closures carried forward.** R1, R3, R5, R6 and R7 remain closed. Their record delivery, world oracle, dependency/input contracts and artifact graph are unchanged. The repair changes no planned game source path, failure program, live-run budget, artifact filename or release member. Planned scope remains 35 pairs, 70 original launches, one replacement, 219 artifacts and 289 release members.

**Checks.** Both checked read-only document commands pass: 43 contract sections and 49 schema definitions; 21 contract mutations and 147 malformed schema objects rejected. These runs corroborate the inspected specification. They do not replace the independent semantic review. No additional build or live evidence was requested or acquired.

**Boundary.** Root closure/native checks are separate development evidence. This reviewer performed no CITY writes, ControlTower calls, builds, live processes, commits, pushes or seals. Actual plugin compilation, startup and live proof remain future implementation obligations after the operator freezes the exact specification and grants the required authority.

**Artifacts.** `review.json` contains the recommendation and closed finding ledger. `checks.json` records argv, timestamps, exits and output hashes. `focused-comparison.json` binds unchanged sections and exact fault-code comparisons. `source-identities.json`, `snapshot-start.json` and `snapshot-end.json` bind this view. `SHA256SUMS.txt` hashes the report and supporting files.
