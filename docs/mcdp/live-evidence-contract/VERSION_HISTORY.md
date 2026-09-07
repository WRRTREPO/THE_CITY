# Version history

Documentation edition: 1. The selected proof remains `Live Cross-Domain Evidence Round-Trip Proof`, version `0.1.0-draft.3`.

The sealed continuation is `0.7.0-draft.83`. Capacity is `0.1.11`. Game Phase 4 is sealed in its original bounded scope. `PHASE_5_FREEZE.json` records the later acceptance of draft 3 at commit `712fff25e3e256a77b733f7ca108aa9d7ad00d1e`. The draft and contract keep their historical review-time labels.

The active checkout is Projects/CITY. The Desktop checkout is preserved reference material. MCDP now verifies the intermediate implementation contract. P16 may seal only `implementation_contract_sealed`. Phoenix must produce the unchanged live acceptance proof.

Do not silently edit this document set after its documentation commit. New doctrine, scenarios or proof boundaries require a versioned successor and a new contract. P15 applicability and the P16 seal record are separate phase artifacts. This P14 manifest does not predeclare their completion.

The exact contract projection follows. Historical review labels remain unchanged.

```json
{
  "schema": "city.mcdp.documentation.v1",
  "document": "VERSION_HISTORY.md",
  "contract_sha256": "b862ceba039b1f2f418b01fe32221f14f095ce4894d163077b4eaa31dd0a8755",
  "projection": {
    "identity": {
      "proof": "Live Cross-Domain Evidence Round-Trip Proof",
      "version": "0.1.0-draft.3",
      "phase": 5,
      "status": "specification_review",
      "implementation_authorized": false,
      "evidence_sealed": false
    },
    "review_gate": {
      "document_validator_proves": "structural_specification_consistency_only",
      "independent_review": "pending",
      "freeze": "pending",
      "mcdp_session": "mcdp-city-live-evidence-spec",
      "phoenix_handoff": "not_created",
      "runtime_proof": "not_run"
    }
  },
  "live_acceptance_verified": false,
  "game_implementation_authorized": false,
  "game_sealed": false,
  "trusted_ci": false
}
```
