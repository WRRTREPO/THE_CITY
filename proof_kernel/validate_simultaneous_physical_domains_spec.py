#!/usr/bin/env python3
"""Validate the unfrozen Phase-3 specification's mechanical review invariants.

This is a review-time document validator. It does not import or execute a
Phase-3 proof implementation and is intentionally outside the prospective
release manifest.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "Simultaneous Physical Domains Proof - Draft.md"
ARTIFACT_ROOT = "proof_kernel/SimultaneousPhysicalDomainsProofRecords"
MANIFEST = "Simultaneous Physical Domains Proof - v0.1.0 SHA256SUMS.txt"
THIS_VALIDATOR = "proof_kernel/validate_simultaneous_physical_domains_spec.py"


class ValidationError(RuntimeError):
    """Raised when the specification violates a frozen review invariant."""


def fenced_block_after(text: str, marker: str, language: str = "yaml") -> str:
    marker_offset = text.find(marker)
    if marker_offset < 0:
        raise ValidationError(f"missing section marker: {marker}")
    fence = f"```{language}\n"
    start = text.find(fence, marker_offset)
    if start < 0:
        raise ValidationError(f"missing {language} fence after: {marker}")
    start += len(fence)
    end = text.find("\n```", start)
    if end < 0:
        raise ValidationError(f"unterminated {language} fence after: {marker}")
    return text[start:end]


def list_members(block: str) -> list[str]:
    return [match.group(1) for match in re.finditer(r"^  - (.+)$", block, re.MULTILINE)]


def top_level_keys(block: str) -> list[str]:
    return [match.group(1) for match in re.finditer(r"^([a-z][a-z0-9_]*):", block, re.MULTILINE)]


def require_all(haystack: str, needles: tuple[str, ...], subject: str) -> None:
    missing = [needle for needle in needles if needle not in haystack]
    if missing:
        raise ValidationError(f"{subject} missing: {', '.join(missing)}")


def require_unique(values: list[str], subject: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValidationError(f"{subject} has duplicates: {duplicates}")


def validate() -> list[str]:
    text = SPEC.read_text(encoding="utf-8")
    checks: list[str] = []

    require_all(
        text,
        (
            "**Version:** 0.1.0-draft.3",
            "freeze_status: not_frozen",
            "implementation_authority: none",
        ),
        "authority header",
    )
    checks.append("authority: draft.3, not frozen, implementation none")

    state_block = fenced_block_after(text, "The only admitted head states are:")
    expected_states = [
        "unbound",
        "synchronized",
        "head_unconfirmed",
        "stale",
        "invalid",
        "protocol_invalid",
    ]
    actual_states = top_level_keys(state_block)
    if actual_states != expected_states:
        raise ValidationError(f"head states {actual_states!r} != {expected_states!r}")
    require_all(
        text,
        (
            "guard open_for_H0 --> synchronized(H0)",
            "closed_for_H0_to_H1 before commit --> head_unconfirmed(accepted H0)",
            "then guard opens_for_H1 --> stale(accepted H0, current H1)",
            "guard_open_at_commit)",
            "protocol_invalid\n  -- proof-local recovery or refresh --> no transition",
        ),
        "head-state transitions",
    )
    checks.append("head state table: exact 6 states and terminal guard-open transition")

    guard_block = fenced_block_after(text, "Its exact states are:")
    require_all(
        guard_block,
        (
            "open_for_H0:",
            "closed_for_H0_to_H1:",
            "open_for_H1:",
            "failed_closed:",
            "reopening: prohibited_in_this_proof",
        ),
        "physical guard",
    )
    require_all(
        text,
        (
            "only normal guard reopening in the proof",
            "classify every still-H0 affected domain as `stale(H0/H1)`",
            "change the guard from `closed_for_H0_to_H1` to `open_for_H1`",
            "`failed_closed` and classify both affected domains",
            "`protocol_invalid(accepted H0, committed H1, guard_open_at_commit)`",
        ),
        "guard transition law",
    )
    checks.append("physical guard: 4 exact states, one reopening, fail-closed control")

    disposition_block = fenced_block_after(
        text, "The harness emits a separate detached disposition"
    )
    require_all(
        disposition_block,
        (
            "head_state: head_unconfirmed | stale | synchronized | invalid | protocol_invalid",
            "refresh_enabled: true_iff_stale_H0_against_verified_H1_and_guard_open_for_H1 | false",
            "current_head_claim_enabled: true_iff_synchronized_to_guard_matching_privately_verified_head | false",
            "current_head_claim_scope: disposable_representation_correspondence_only | none",
            "canonical_evidence_enabled: false",
            "canonical_scheduling_enabled: false",
            "canonical_mutation_enabled: false",
        ),
        "disposition schema",
    )
    if "current_head_claim_enabled: false\n" in disposition_block:
        raise ValidationError("disposition hardcodes every current-head claim false")
    require_all(
        state_block,
        (
            "current_head_materialization_claim: permitted_as_harness_accepted_representation_only",
            "claim_authority: disposable_representation_correspondence_only",
        ),
        "synchronized state",
    )
    for matrix_row in (
        "| `synchronized(H0)` | `open_for_H0` | enabled, representation-only | disabled |",
        "| `head_unconfirmed(H0)` | `closed_for_H0_to_H1` or `failed_closed` | disabled | disabled |",
        "| `stale(H0/H1)` | `open_for_H1` | disabled | exact H1 once |",
        "| `synchronized(H1)` | `open_for_H1` | enabled, representation-only | disabled |",
        "| `invalid` | any matching recorded state | disabled | disabled |",
        "| `protocol_invalid(H0/H1)` | `failed_closed` | disabled | disabled |",
    ):
        if matrix_row not in text:
            raise ValidationError(f"permission matrix missing row: {matrix_row}")
    checks.append("disposition: synchronized representation claim aligned; authority paths false")

    semantic_block = fenced_block_after(text, "The exact proof-semantic closure is:")
    require_all(
        semantic_block,
        (
            "proof_semantic_inputs:",
            "semantic_environment_keys: []",
            "semantic_command_line_selectors: []",
            "prohibited_hidden_semantic_inputs:",
            "current_head_observation_path_or_bytes",
            "physical_current_head_guard_state",
            "harness_head_state_classification",
            "harness_refresh_eligibility",
            "expected_physical_access_result",
            "other_domain_root_or_state",
            "project_Content_ProofRecords",
            "environment_or_argv_proof_selector",
            "inherited_or_runtime_opened_alternate_command_channel",
        ),
        "proof-semantic input closure",
    )
    semantic_positive = semantic_block.partition("  prohibited_hidden_semantic_inputs:")[0]
    for forbidden_positive_input in (
        "current_head_observation",
        "physical_current_head_guard",
        "harness_head_state",
        "harness_refresh_eligibility",
        "expected_physical_access_result",
    ):
        if forbidden_positive_input in semantic_positive:
            raise ValidationError(
                f"hidden input appears in positive semantic closure: {forbidden_positive_input}"
            )
    launch_block = fenced_block_after(text, "The complete launch-surface audit is exact:")
    require_all(
        launch_block,
        (
            "argv_in_order:",
            "environment:",
            "cwd:",
            "inherited_descriptors:",
            "executable_project_and_runtime:",
            "proof_semantic_key_allowlist: []",
            "all_other_descriptors_at_exec: closed",
            "unreal_engine_build_and_entry_map_identity: recorded_and_binding_verified",
            "engine_and_system_loaded_image_inventory: realpath_UUID_and_raw_hash_recorded",
            "initial_world_actor_class_inventory_before_first_materialization: recorded",
            "non_Phase3_world_actor_reads_for_proof_semantics: prohibited",
            "project_Content_ProofRecords_reads: prohibited",
        ),
        "launch-surface audit",
    )
    for impossible_literal in (
        "other_files_or_context: none",
        "unreal_visible_inputs:",
        "The complete information visible to either Unreal process is closed as:",
    ):
        if impossible_literal in text:
            raise ValidationError(f"impossible process-visibility claim remains: {impossible_literal}")
    checks.append("proof-semantic closure: launch/runtime surfaces audited; hidden inputs prohibited")

    artifact_block = fenced_block_after(
        text, "That directory must contain exactly these 44 regular files"
    )
    artifacts = list_members(artifact_block)
    if len(artifacts) != 44:
        raise ValidationError(f"artifact count {len(artifacts)} != 44")
    require_unique(artifacts, "artifact names")
    checks.append("release artifacts: 44 exact unique names")

    member_block = fenced_block_after(
        text, "The manifest member set is the union of the exact 44 artifact paths above"
    )
    governing_members = list_members(member_block)
    if len(governing_members) != 66:
        raise ValidationError(f"non-artifact manifest count {len(governing_members)} != 66")
    require_unique(governing_members, "non-artifact manifest members")
    artifact_paths = [f"{ARTIFACT_ROOT}/{name}" for name in artifacts]
    manifest_members = artifact_paths + governing_members
    if len(manifest_members) != 110:
        raise ValidationError(f"manifest count {len(manifest_members)} != 110")
    require_unique(manifest_members, "complete manifest members")
    if MANIFEST in manifest_members:
        raise ValidationError("self-excluding manifest includes itself")
    if THIS_VALIDATOR in manifest_members:
        raise ValidationError("review-time validator entered release manifest")
    require_all(
        text,
        (
            "Its 110 member lines must be the complete union above",
            "It must exclude itself.",
            "review-time document validator",
            "specification QA only",
        ),
        "self-excluding manifest contract",
    )
    checks.append("release manifest: 44 + 66 = 110 unique members; manifest self-excluded")

    return checks


def main() -> int:
    try:
        checks = validate()
    except (OSError, UnicodeError, ValidationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    for index, check in enumerate(checks, start=1):
        print(f"PASS {index}: {check}")
    print(f"RESULT: PASS ({len(checks)}/{len(checks)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
