#!/usr/bin/env python3
"""Validate the frozen Phase-3 specification's mechanical contract invariants.

This is a review-time document validator. It does not import or execute a
Phase-3 proof implementation and is intentionally outside the prospective
release manifest. ``--self-test`` mutates only in-memory document copies.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "Simultaneous Physical Domains Proof - Draft.md"
ARTIFACT_ROOT = "proof_kernel/SimultaneousPhysicalDomainsProofRecords"
MANIFEST = "Simultaneous Physical Domains Proof - v0.1.0 SHA256SUMS.txt"
THIS_VALIDATOR = "proof_kernel/validate_simultaneous_physical_domains_spec.py"

EXPECTED_SELECTION = (
    ("phase", "3"),
    ("proof", "Simultaneous Physical Domains Proof"),
    ("version", "0.1.0"),
    ("status", "frozen_specification"),
    ("implementation_authority", "bounded_phase_3_proof_only"),
    ("unreal_source_change_authority", "exact_frozen_phase_3_paths_only"),
    ("capacity_advancement", "none"),
    ("freeze_status", "frozen"),
    ("evidence_status", "unsealed"),
)
EXPECTED_CURRENT_DECISION = (
    ("working_unit", "Simultaneous Physical Domains Proof v0.1.0 bounded implementation"),
    ("successor_selected", "true"),
    ("specification_status", "frozen"),
    ("freeze_status", "frozen"),
    ("implementation_authority", "bounded_phase_3_proof_only"),
    ("canonical_capacity_change", "none"),
    ("evidence_status", "unsealed"),
    (
        "latest_sealed_capacity",
        "THE_CITY Development Capacity and Progress Note v0.1.11",
    ),
)
EXPECTED_HEAD_STATES = (
    "unbound",
    "synchronized",
    "head_unconfirmed",
    "stale",
    "invalid",
    "protocol_invalid",
)
EXPECTED_GUARD_STATES = (
    "open_for_H0",
    "closed_for_H0_to_H1",
    "open_for_H1",
    "failed_closed",
)
EXPECTED_SEMANTIC_GROUPS = (
    "immutable_process_binding",
    "adapter_launch_tuple",
    "stdin_commands_in_exact_order",
    "adapter_refresh_tuple",
    "probe_live_state",
    "executable_and_project_dependencies",
    "semantic_environment_keys",
    "semantic_command_line_selectors",
    "semantic_inherited_descriptors",
    "prohibited_hidden_semantic_inputs",
)
EXPECTED_DISPOSITION_FIELDS = (
    "disposition_schema",
    "proof_scenario",
    "domain_role",
    "operational_process_instance_id",
    "process_binding_raw_sha256",
    "representation_receipt_raw_sha256",
    "physical_observation_raw_sha256",
    "represented_canonical_hash",
    "harness_observed_current_canonical_hash",
    "physical_current_head_guard_state",
    "head_state",
    "refresh_enabled",
    "current_head_claim_enabled",
    "current_head_claim_scope",
    "canonical_evidence_enabled",
    "canonical_scheduling_enabled",
    "canonical_mutation_enabled",
)
EXPECTED_PERMISSION_TABLE = (
    "| Head state | Required guard | Current-head representation claim | Refresh | Local execution |",
    "| --- | --- | --- | --- | --- |",
    "| `synchronized(H0)` | `open_for_H0` | enabled, representation-only | disabled | nonconsequential permitted |",
    "| `head_unconfirmed(H0)` | `closed_for_H0_to_H1` or `failed_closed` | disabled | disabled | quarantined nonconsequential permitted |",
    "| `stale(H0/H1)` | `open_for_H1` | disabled | exact H1 once | quarantined nonconsequential permitted |",
    "| `synchronized(H1)` | `open_for_H1` | enabled, representation-only | disabled | nonconsequential permitted |",
    "| `invalid` | any matching recorded state | disabled | disabled | halted; diagnostics/termination only |",
    "| `protocol_invalid(H0/H1)` | `failed_closed` | disabled | disabled | halted; diagnostics/termination only |",
)
REQUIRED_REFRESH_FAULT_LIFECYCLE = (
    "The exact refresh stages frozen for mandatory pre/post fault injection during "
    "the later authorized implementation/evidence phase are:"
)
PROHIBITED_OLD_REFRESH_FAULT_LIFECYCLE = (
    "The exact refresh stages that require pre/post fault injection before freeze are:"
)
PREFREEZE_TERMS = re.compile(
    r"\b(?:before|prior to)\s+(?:a\s+)?(?:separately reviewed\s+)?freeze\b|\bpre[- ]freeze\b",
    re.IGNORECASE,
)
PHASE_3_EXECUTION_TERMS = re.compile(
    r"\b(?:phase[- ]?3\s+execution|proof\s+execution|runtime|harness|"
    r"unreal\s+execution|fault[- ]injection|refresh\s+fault\s+stages?)\b",
    re.IGNORECASE,
)
OBLIGATION_TERMS = re.compile(
    r"\b(?:must|shall|mandatory|required|requires?|has\s+to|have\s+to|"
    r"needs?\s+to|is\s+to|are\s+to|occurs?|runs?|executes?|"
    r"is\s+performed|are\s+performed|is\s+executed|are\s+executed)\b",
    re.IGNORECASE,
)

# These digests bind complete ordered structures, not selected phrases. They are
# filled from the reviewed Draft.4 blocks and deliberately fail on any byte,
# field, member, order, or whitespace change inside those structures.
EXPECTED_BLOCK_SHA256 = {
    "head_state": "40e676d86da83ea8de39c88e6507663a01c0f382d4e3337e2fe9d4ef9b91b9f8",
    "guard": "802007f0e1a21d56b98e071a66bed25dea43410b324f2e1b5902b296382d3730",
    "disposition": "87a3fa65127cfbd4bae85a2f5fb5c86ed62011917219a937c0e68b6f784d1b3a",
    "semantic": "c02b3d39c7e7c290d48e68a0aa5ea1d6794197e2a521990d86cb8dafaaaf5bbc",
    "launch": "5f9f1f13ec37217bc6c95fae1753f2074f00e7630c420f1f330ea0ec9e539f30",
    "artifact_block": "931105d9b0f7bfbce84a3b93eef330185f19e80724e52b6a9bf17790990b2cee",
    "member_block": "cf110b78f78c6c96df045744600435a22170f4aab4d94946fdd7fd2f84b4802b",
    "implementation_authority": "b5434b2c4497b973c37f308c01247b1c9c8cad4dcaa12c95359478524b9ca3cc",
}
EXPECTED_ARTIFACT_LIST_SHA256 = "f46388d2f0842121de2a88ff6931b095f8a29eadf727833bb7f0eef4d894ac5c"
EXPECTED_NON_ARTIFACT_MEMBER_LIST_SHA256 = (
    "a2422bee7f6bf1d0ea70531452b640fe1b02fdd0c879894c57c172ceaa1773ef"
)


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


def rewrite_fenced_block(
    text: str,
    marker: str,
    transform: Callable[[str], str],
    language: str = "yaml",
) -> str:
    marker_offset = text.find(marker)
    if marker_offset < 0:
        raise AssertionError(f"self-test marker missing: {marker}")
    fence = f"```{language}\n"
    start = text.find(fence, marker_offset)
    if start < 0:
        raise AssertionError(f"self-test fence missing after: {marker}")
    start += len(fence)
    end = text.find("\n```", start)
    if end < 0:
        raise AssertionError(f"self-test fence unterminated after: {marker}")
    old_block = text[start:end]
    new_block = transform(old_block)
    if old_block == new_block:
        raise AssertionError(f"self-test mutation made no change after: {marker}")
    return text[:start] + new_block + text[end:]


def replace_once(value: str, old: str, new: str) -> str:
    if value.count(old) != 1:
        raise AssertionError(f"self-test target count for {old!r} is {value.count(old)}")
    return value.replace(old, new, 1)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def ordered_list_sha256(values: list[str]) -> str:
    encoded = json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def list_members(block: str) -> list[str]:
    return [match.group(1) for match in re.finditer(r"^  - (.+)$", block, re.MULTILINE)]


def top_level_keys(block: str) -> list[str]:
    return [match.group(1) for match in re.finditer(r"^([a-z][a-z0-9_]*):", block, re.MULTILINE)]


def nested_mapping_keys(block: str) -> list[str]:
    return [
        match.group(1)
        for match in re.finditer(r"^  ([A-Za-z][A-Za-z0-9_]*):(?: .*)?$", block, re.MULTILINE)
    ]


def parse_flat_mapping(block: str, subject: str, root: str | None = None) -> list[tuple[str, str]]:
    lines = block.splitlines()
    if root is not None:
        if not lines or lines[0] != f"{root}:":
            raise ValidationError(f"{subject} root must be exactly {root!r}")
        lines = lines[1:]
        prefix = "  "
    else:
        prefix = ""
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in lines:
        if not line or not line.startswith(prefix):
            raise ValidationError(f"{subject} contains malformed line: {line!r}")
        content = line[len(prefix) :]
        if content.startswith(" ") or ": " not in content:
            raise ValidationError(f"{subject} contains nested or valueless line: {line!r}")
        key, value = content.split(": ", 1)
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            raise ValidationError(f"{subject} contains invalid key: {key!r}")
        if key in seen:
            raise ValidationError(f"{subject} contains duplicate key: {key}")
        seen.add(key)
        result.append((key, value))
    return result


def markdown_table_after(text: str, marker: str) -> tuple[str, ...]:
    offset = text.find(marker)
    if offset < 0:
        raise ValidationError(f"missing table marker: {marker}")
    lines = text[offset:].splitlines()
    table: list[str] = []
    started = False
    for line in lines[1:]:
        if line.startswith("|"):
            started = True
            table.append(line)
        elif started:
            break
    if not table:
        raise ValidationError(f"missing table after: {marker}")
    return tuple(table)


def require_exact_digest(block: str, key: str, subject: str) -> None:
    actual = sha256_text(block)
    expected = EXPECTED_BLOCK_SHA256[key]
    if actual != expected:
        raise ValidationError(f"{subject} digest {actual} != {expected}")


def require_unique(values: list[str], subject: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValidationError(f"{subject} has duplicates: {duplicates}")


def prefreeze_runtime_obligation_clauses(text: str) -> list[str]:
    """Return prose clauses that require Phase-3 execution before freeze."""

    normalized = re.sub(r"\s+", " ", text)
    clauses = re.split(r"(?<=[.:])\s+", normalized)
    return [
        clause
        for clause in clauses
        if PREFREEZE_TERMS.search(clause)
        and PHASE_3_EXECUTION_TERMS.search(clause)
        and OBLIGATION_TERMS.search(clause)
    ]


def validate_text(text: str) -> list[str]:
    checks: list[str] = []

    selection_block = fenced_block_after(text, "## Selection and authority state")
    selection = parse_flat_mapping(selection_block, "selection authority", root="selection")
    if tuple(selection) != EXPECTED_SELECTION:
        raise ValidationError(f"selection authority {selection!r} != {EXPECTED_SELECTION!r}")
    decision_block = fenced_block_after(text, "## Current decision record")
    decision = parse_flat_mapping(decision_block, "current decision")
    if tuple(decision) != EXPECTED_CURRENT_DECISION:
        raise ValidationError(f"current decision {decision!r} != {EXPECTED_CURRENT_DECISION!r}")
    if "**Version:** 0.1.0" not in text:
        raise ValidationError("active version header is not frozen v0.1.0")
    checks.append("authority: frozen v0.1.0; bounded implementation; capacity none")

    authority_surface = fenced_block_after(text, "The exact bounded implementation surface is:")
    if top_level_keys(authority_surface) != ["frozen_implementation_authority"]:
        raise ValidationError("frozen implementation authority root is not exact")
    require_exact_digest(
        authority_surface,
        "implementation_authority",
        "frozen implementation authority block",
    )
    checks.append("implementation surface: exact bounded paths and no capacity advancement")

    state_block = fenced_block_after(text, "The only admitted head states are:")
    actual_states = tuple(top_level_keys(state_block))
    if actual_states != EXPECTED_HEAD_STATES:
        raise ValidationError(f"head states {actual_states!r} != {EXPECTED_HEAD_STATES!r}")
    require_exact_digest(state_block, "head_state", "head-state block")
    checks.append("head state table: exact ordered six-state structure")

    guard_block = fenced_block_after(text, "Its exact states are:")
    guard_root = top_level_keys(guard_block)
    if guard_root != ["physical_current_head_guard"]:
        raise ValidationError(f"physical guard root is not exact: {guard_root!r}")
    guard_states = tuple(nested_mapping_keys(guard_block))
    if guard_states != EXPECTED_GUARD_STATES:
        raise ValidationError(f"guard states {guard_states!r} != {EXPECTED_GUARD_STATES!r}")
    require_exact_digest(guard_block, "guard", "physical guard block")
    checks.append("physical guard: exact ordered four-state structure")

    disposition_block = fenced_block_after(
        text, "The harness emits a separate detached disposition"
    )
    disposition = parse_flat_mapping(disposition_block, "disposition schema")
    disposition_fields = tuple(key for key, _ in disposition)
    if disposition_fields != EXPECTED_DISPOSITION_FIELDS:
        raise ValidationError(
            f"disposition fields {disposition_fields!r} != {EXPECTED_DISPOSITION_FIELDS!r}"
        )
    require_exact_digest(disposition_block, "disposition", "disposition schema")
    permission_table = markdown_table_after(text, "The exact permission matrix is:")
    if permission_table != EXPECTED_PERMISSION_TABLE:
        raise ValidationError("permission matrix differs from exact ordered rows")
    checks.append("disposition: exact schema and permission matrix")

    semantic_block = fenced_block_after(text, "The exact proof-semantic closure is:")
    semantic_root = top_level_keys(semantic_block)
    if semantic_root != ["proof_semantic_inputs"]:
        raise ValidationError(f"proof-semantic root is not exact: {semantic_root!r}")
    semantic_groups = tuple(nested_mapping_keys(semantic_block))
    if semantic_groups != EXPECTED_SEMANTIC_GROUPS:
        raise ValidationError(
            f"proof-semantic groups {semantic_groups!r} != {EXPECTED_SEMANTIC_GROUPS!r}"
        )
    require_exact_digest(semantic_block, "semantic", "proof-semantic input block")
    launch_block = fenced_block_after(text, "The complete launch-surface audit is exact:")
    require_exact_digest(launch_block, "launch", "launch-surface block")
    for impossible_literal in (
        "other_files_or_context: none",
        "unreal_visible_inputs:",
        "The complete information visible to either Unreal process is closed as:",
    ):
        if impossible_literal in text:
            raise ValidationError(f"impossible process-visibility claim remains: {impossible_literal}")
    checks.append("proof-semantic and launch surfaces: exact ordered structures")

    normalized_text = re.sub(r"\s+", " ", text)
    if normalized_text.count(REQUIRED_REFRESH_FAULT_LIFECYCLE) != 1:
        raise ValidationError("correct refresh-fault lifecycle wording must occur exactly once")
    if PROHIBITED_OLD_REFRESH_FAULT_LIFECYCLE in normalized_text:
        raise ValidationError("old pre-freeze refresh-fault obligation remains")
    prohibited_clauses = prefreeze_runtime_obligation_clauses(text)
    if prohibited_clauses:
        raise ValidationError(
            "Phase-3 runtime execution is required before freeze: "
            + repr(prohibited_clauses[0])
        )
    checks.append("refresh fault lifecycle: later authorized execution only")

    artifact_block = fenced_block_after(
        text, "That directory must contain exactly these 44 regular files"
    )
    artifacts = list_members(artifact_block)
    require_exact_digest(artifact_block, "artifact_block", "artifact member block")
    if len(artifacts) != 44:
        raise ValidationError(f"artifact count {len(artifacts)} != 44")
    require_unique(artifacts, "artifact names")
    artifact_digest = ordered_list_sha256(artifacts)
    if artifact_digest != EXPECTED_ARTIFACT_LIST_SHA256:
        raise ValidationError(
            f"ordered artifact list digest {artifact_digest} != {EXPECTED_ARTIFACT_LIST_SHA256}"
        )
    checks.append("release artifacts: exact ordered 44-member set")

    member_block = fenced_block_after(
        text, "The manifest member set is the union of the exact 44 artifact paths above"
    )
    governing_members = list_members(member_block)
    require_exact_digest(member_block, "member_block", "non-artifact member block")
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
    member_digest = ordered_list_sha256(governing_members)
    if member_digest != EXPECTED_NON_ARTIFACT_MEMBER_LIST_SHA256:
        raise ValidationError(
            "ordered non-artifact member list digest "
            f"{member_digest} != {EXPECTED_NON_ARTIFACT_MEMBER_LIST_SHA256}"
        )
    checks.append("release manifest: exact 44 + 66 = 110 set; self-exclusions enforced")

    required_frozen_authority = (
        "The specification is frozen. Implementation authority is limited to the exact "
        "Phase-3 proof paths and bounded dispatch branch declared by this contract."
    )
    if normalized_text.count(required_frozen_authority) != 1:
        raise ValidationError("frozen bounded-authority sentence must occur exactly once")
    if (
        "The review-time document validator is the sole pre-freeze QA-code exception."
        in normalized_text
    ):
        raise ValidationError("obsolete pre-freeze validator exception remains active")
    if "No code may be written for this proof until" in text:
        raise ValidationError("obsolete pre-freeze no-code sentence remains")
    checks.append("authority prose: frozen bounded implementation and unsealed evidence aligned")

    return checks


def validate() -> list[str]:
    return validate_text(SPEC.read_text(encoding="utf-8"))


def mutate_block_replace(text: str, marker: str, old: str, new: str) -> str:
    return rewrite_fenced_block(text, marker, lambda block: replace_once(block, old, new))


def guard_without_open_h1(block: str) -> str:
    start = block.find("  open_for_H1:\n")
    end = block.find("  failed_closed:\n")
    if start < 0 or end < 0 or end <= start:
        raise AssertionError("guard self-test could not isolate open_for_H1")
    return block[:start] + block[end:]


def guard_reordered(block: str) -> str:
    first = block.find("  open_for_H0:\n")
    second = block.find("  closed_for_H0_to_H1:\n")
    third = block.find("  open_for_H1:\n")
    if min(first, second, third) < 0 or not first < second < third:
        raise AssertionError("guard self-test could not isolate first two states")
    return block[:first] + block[second:third] + block[first:second] + block[third:]


def semantic_reordered(block: str) -> str:
    first = block.find("  immutable_process_binding:\n")
    second = block.find("  adapter_launch_tuple:\n")
    third = block.find("  stdin_commands_in_exact_order:\n")
    if min(first, second, third) < 0 or not first < second < third:
        raise AssertionError("semantic self-test could not isolate first two groups")
    return block[:first] + block[second:third] + block[first:second] + block[third:]


def swap_first_two_list_members(block: str) -> str:
    matches = list(re.finditer(r"^  - .+$", block, re.MULTILINE))
    if len(matches) < 2:
        raise AssertionError("list self-test needs two members")
    first = matches[0].group(0)
    second = matches[1].group(0)
    return replace_once(block, f"{first}\n{second}", f"{second}\n{first}")


def self_test_mutations(text: str) -> list[tuple[str, str]]:
    selection_marker = "## Selection and authority state"
    authority_surface_marker = "The exact bounded implementation surface is:"
    guard_marker = "Its exact states are:"
    semantic_marker = "The exact proof-semantic closure is:"
    artifact_marker = "That directory must contain exactly these 44 regular files"
    member_marker = "The manifest member set is the union of the exact 44 artifact paths above"

    mutations: list[tuple[str, str]] = []
    mutations.append(
        (
            "extra_authority_field",
            mutate_block_replace(
                text,
                selection_marker,
                "selection:\n",
                "selection:\n  undeclared_authority: none\n",
            ),
        )
    )
    mutations.append(
        (
            "missing_authority_field",
            mutate_block_replace(text, selection_marker, "  capacity_advancement: none\n", ""),
        )
    )
    mutations.append(
        (
            "duplicate_contradictory_authority",
            mutate_block_replace(
                text,
                selection_marker,
                "  implementation_authority: bounded_phase_3_proof_only\n",
                "  implementation_authority: bounded_phase_3_proof_only\n"
                "  implementation_authority: unbounded_production_runtime\n",
            ),
        )
    )
    mutations.append(
        (
            "unbounded_implementation_authority",
            mutate_block_replace(
                text,
                selection_marker,
                "  implementation_authority: bounded_phase_3_proof_only",
                "  implementation_authority: unbounded_production_runtime",
            ),
        )
    )
    mutations.append(
        (
            "unfrozen_phase_3_authority_state",
            mutate_block_replace(
                text,
                selection_marker,
                "  freeze_status: frozen",
                "  freeze_status: not_frozen",
            ),
        )
    )
    mutations.append(
        (
            "additional_authorized_source_path",
            mutate_block_replace(
                text,
                authority_surface_marker,
                "  new_python_paths:\n",
                "  new_python_paths:\n    - proof_kernel/forbidden_extra_runtime.py\n",
            ),
        )
    )
    mutations.append(
        (
            "old_fault_injection_before_freeze_wording",
            replace_once(
                text,
                REQUIRED_REFRESH_FAULT_LIFECYCLE,
                PROHIBITED_OLD_REFRESH_FAULT_LIFECYCLE,
            ),
        )
    )
    mutations.append(
        (
            "mandatory_harness_execution_before_freeze",
            replace_once(
                text,
                REQUIRED_REFRESH_FAULT_LIFECYCLE,
                "Phase-3 harness execution is mandatory before freeze:",
            ),
        )
    )
    mutations.append(
        (
            "proof_runtime_must_execute_before_freeze",
            replace_once(
                text,
                REQUIRED_REFRESH_FAULT_LIFECYCLE,
                "Before freeze, the proof runtime must execute every refresh fault stage:",
            ),
        )
    )
    mutations.append(
        (
            "reordered_authority_fields",
            mutate_block_replace(
                text,
                selection_marker,
                "  phase: 3\n  proof: Simultaneous Physical Domains Proof",
                "  proof: Simultaneous Physical Domains Proof\n  phase: 3",
            ),
        )
    )
    mutations.append(
        (
            "extra_guard_state",
            rewrite_fenced_block(
                text,
                guard_marker,
                lambda block: block
                + "\n  unexpected_guard_state:\n"
                + "    accepted_physical_head: none\n"
                + "    current_head_representation_claim_acceptance: false\n"
                + "    refresh_eligibility: false",
            ),
        )
    )
    mutations.append(
        ("missing_guard_state", rewrite_fenced_block(text, guard_marker, guard_without_open_h1))
    )
    mutations.append(
        ("reordered_guard_states", rewrite_fenced_block(text, guard_marker, guard_reordered))
    )
    mutations.append(
        (
            "extra_positive_semantic_input",
            mutate_block_replace(
                text,
                semantic_marker,
                "  prohibited_hidden_semantic_inputs:\n",
                "  undeclared_positive_input:\n"
                "    - forbidden_context\n"
                "  prohibited_hidden_semantic_inputs:\n",
            ),
        )
    )
    mutations.append(
        (
            "missing_positive_semantic_member",
            mutate_block_replace(text, semantic_marker, "    - exact R0 bytes\n", ""),
        )
    )
    mutations.append(
        (
            "reordered_positive_semantic_groups",
            rewrite_fenced_block(text, semantic_marker, semantic_reordered),
        )
    )
    permission_row = EXPECTED_PERMISSION_TABLE[2]
    mutations.append(
        (
            "altered_permission_row",
            replace_once(
                text,
                permission_row,
                permission_row.replace("enabled, representation-only", "disabled", 1),
            ),
        )
    )
    artifacts = list_members(fenced_block_after(text, artifact_marker))
    mutations.append(
        (
            "duplicate_artifact_member",
            mutate_block_replace(text, artifact_marker, artifacts[1], artifacts[0]),
        )
    )
    mutations.append(
        (
            "additional_artifact_member",
            rewrite_fenced_block(
                text,
                artifact_marker,
                lambda block: block + "\n  - forbidden_additional_artifact.json",
            ),
        )
    )
    mutations.append(
        (
            "reordered_artifact_members",
            rewrite_fenced_block(text, artifact_marker, swap_first_two_list_members),
        )
    )
    members = list_members(fenced_block_after(text, member_marker))
    mutations.append(
        (
            "duplicate_manifest_member",
            mutate_block_replace(text, member_marker, members[1], members[0]),
        )
    )
    mutations.append(
        (
            "additional_manifest_member",
            rewrite_fenced_block(
                text, member_marker, lambda block: block + "\n  - forbidden/additional-member"
            ),
        )
    )
    mutations.append(
        (
            "reordered_manifest_members",
            rewrite_fenced_block(text, member_marker, swap_first_two_list_members),
        )
    )
    mutations.append(
        (
            "validator_self_inclusion",
            mutate_block_replace(
                text,
                member_marker,
                f"  - {members[0]}",
                f"  - {THIS_VALIDATOR}",
            ),
        )
    )
    mutations.append(
        (
            "manifest_self_inclusion",
            mutate_block_replace(
                text,
                member_marker,
                f"  - {members[0]}",
                f"  - {MANIFEST}",
            ),
        )
    )
    return mutations


def run_self_tests() -> list[str]:
    text = SPEC.read_text(encoding="utf-8")
    validate_text(text)
    results = ["baseline active document accepted"]
    for name, mutated in self_test_mutations(text):
        if mutated == text:
            raise AssertionError(f"self-test {name} did not mutate the document")
        try:
            validate_text(mutated)
        except ValidationError:
            results.append(f"rejected {name}")
        else:
            raise ValidationError(f"self-test mutation was incorrectly accepted: {name}")
    return results


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        if not arguments:
            checks = validate()
            for index, check in enumerate(checks, start=1):
                print(f"PASS {index}: {check}")
            print(f"RESULT: PASS ({len(checks)}/{len(checks)})")
            return 0
        if arguments == ["--self-test"]:
            checks = run_self_tests()
            for index, check in enumerate(checks, start=1):
                print(f"PASS SELF-TEST {index}: {check}")
            rejected = len(checks) - 1
            print(f"RESULT: PASS ({rejected}/{rejected} adversarial mutations rejected)")
            return 0
        print("usage: validate_simultaneous_physical_domains_spec.py [--self-test]", file=sys.stderr)
        return 2
    except (AssertionError, OSError, UnicodeError, ValidationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
