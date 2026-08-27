"""Verifier scaffolding for the frozen Integrated Unreal lifecycle proof.

``canonical`` verifies the completed canonical/reference substrate. ``verify``
is intentionally unavailable until the physical UE primary/return receipts and
their evidence document exist; it must never manufacture those witnesses.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from integrated_unreal_promotion_unload_repromotion import (
    ACTOR_ID,
    NO_EXECUTION_BOUNDARY,
    all_witness_runs,
    canonical_hash,
    equivalence_oracle,
    initial_canonical_envelope,
    proof_run,
    runtime_fail_closed_results,
    source_audit,
    write_artifacts,
)
from kernel import canonical_json


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).with_name("IntegratedUnrealPromotionUnloadRepromotionProofRecords")
EVIDENCE = ROOT / "Integrated Unreal Promotion-Unload-Repromotion Proof Evidence - v0.1.0.md"
MANIFEST = ROOT / "Integrated Unreal Promotion-Unload-Repromotion Proof - v0.1.0 SHA256SUMS.txt"


def _load(name: str) -> Any:
    return json.loads((RECORDS / name).read_text(encoding="utf-8"))


def canonical_source_audit() -> dict[str, Any]:
    """Audit the new source paths, not legacy materialization fixtures."""

    adapter = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.cpp").read_text(encoding="utf-8")
    gate = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.cpp").read_text(encoding="utf-8")
    game_mode = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp").read_text(encoding="utf-8")
    return {
        "adapter_validates_raw_sha256_before_parse": "Sha256Hex(PayloadBytes.GetData(), PayloadBytes.Num())" in adapter,
        "adapter_emits_detached_acceptance_receipt": "INTEGRATED_MATERIALIZATION_RECEIPT:" in adapter,
        "adapter_has_no_canonical_resolver": "resolve_execution_boundary" not in adapter,
        "adapter_has_no_canonical_ledger_write": "authoritative_causal_ledger" not in adapter,
        "adapter_has_no_policy_selection": "next_execution_boundary" not in adapter,
        "gate_writes_only_q": "physical_disable_integrated_gate_token_0001.json" in gate and "committed_record" not in gate and "causal_ledger" not in gate,
        "gate_emits_exact_fixture_actor": ACTOR_ID in gate,
        "gate_q_uses_canonical_key_order": gate.find("\\\"proposed_mutations\\\"") < gate.find("\\\"protocol_version\\\""),
        "integrated_mode_bypasses_legacy_materializer": "AIntegratedUnrealProofAdapter" in game_mode and "IntegratedProofPayload=" in game_mode,
        "source_and_return_context_are_distinct": "IntegratedProofInteractionOpportunity=" in adapter and "bReturnRecord" in adapter,
    }


def verify_canonical() -> None:
    expected = proof_run()
    if canonical_json(_load("integrated_unreal_R0.json")) != canonical_json(expected["r0"]):
        raise ValueError("R0 cannot be regenerated from the frozen fixture")
    for label, expected_record in (("Rinput", expected["rinput"]), ("Rfinal", expected["rfinal"]), ("Rcontrol", expected["rcontrol"])):
        if canonical_json(_load(f"integrated_unreal_{label}.json")) != canonical_json(expected_record):
            raise ValueError(f"{label} cannot be regenerated from the frozen resolver")
    if canonical_json(_load("integrated_unreal_Q.json")) != canonical_json(expected["q"]):
        raise ValueError("frozen Q artifact drift")
    for name, run in expected["witness_runs"].items():
        if canonical_json(_load(f"integrated_unreal_{name}_run.json")) != canonical_json(run):
            raise ValueError(f"{name} run drift")
    if _load("integrated_unreal_equivalence_oracle.json") != expected["equivalence_oracle"]:
        raise ValueError("equivalence oracle drift")
    if _load("integrated_unreal_runtime_fail_closed.json") != expected["runtime_fail_closed"]:
        raise ValueError("runtime fail-closed artifact drift")
    if _load("integrated_unreal_source_audit.json") != expected["source_audit"]:
        raise ValueError("canonical source audit artifact drift")
    if canonical_json(_load("integrated_unreal_proof_run.json")) != canonical_json(expected):
        raise ValueError("canonical proof-run artifact drift")
    if equivalence_oracle(all_witness_runs()) != {"result": "accepted", "reference_witness": "dense_reference", "failures": []}:
        raise ValueError("dense and boundary-jump witnesses diverge")
    if expected["rfinal"]["causal_provenance"]["canonical_ancestry"]["parent_record_hash"] != canonical_hash(expected["rinput"]):
        raise ValueError("Rfinal ancestry is not Rinput-relative")
    if expected["rfinal"]["causal_provenance"]["authoritative_causal_ledger"][-1]["evaluated_gates"][0]["observed_value"] != "disabled":
        raise ValueError("alpha did not read Rinput gate state")
    if all_witness_runs()["dense_reference"]["next_execution_boundary"] != NO_EXECUTION_BOUNDARY:
        raise ValueError("Rfinal retains executable work")
    expected_failures = {
        "digest_changed_without_recompute",
        "redirected_with_recomputed_digest",
        "stale_bq",
        "stale_alpha",
        "local_authority",
    }
    if set(runtime_fail_closed_results()) != expected_failures:
        raise ValueError("runtime rejection surface drift")
    if not all(canonical_source_audit().values()):
        raise ValueError("UE authority source audit failed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write-canonical", "canonical", "verify"))
    args = parser.parse_args()
    if args.command == "write-canonical":
        write_artifacts(RECORDS)
        verify_canonical()
        print("verified canonical fixture artifacts; physical UE lifecycle evidence remains required")
        return 0
    verify_canonical()
    if args.command == "canonical":
        print("verified canonical fixture artifacts; physical UE lifecycle evidence remains required")
        return 0
    if not EVIDENCE.is_file() or not MANIFEST.is_file():
        raise SystemExit("release verification unavailable: physical UE lifecycle evidence has not been sealed")
    raise SystemExit("release verifier wiring is intentionally withheld until actual UE receipt artifacts are present")


if __name__ == "__main__":
    raise SystemExit(main())
