"""Frozen obligation compiler for the live evidence round-trip implementation.

This module compiles the accepted policy. It does not acquire evidence, publish
canonical state, launch Unreal, or certify a release. The harness and independent
release verifier must implement and discharge the compiled obligations.
"""

import hashlib
import json
import math
import re


FROZEN_CONTRACT_SHA256 = (
    "b862ceba039b1f2f418b01fe32221f14f095ce4894d163077b4eaa31dd0a8755"
)


def _reject_constants(value):
    raise ValueError("lcer.nonfinite_json:" + value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("lcer.duplicate_json_key:" + key)
        result[key] = value
    return result


def _load_frozen_policy(raw):
    if type(raw) is not bytes:
        raise ValueError("lcer.contract_bytes_required")
    if hashlib.sha256(raw).hexdigest() != FROZEN_CONTRACT_SHA256:
        raise ValueError("lcer.frozen_contract_mismatch")
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constants,
    )


def _plan_bytes(value):
    """Use the frozen detached-JSON storage convention for the plan digest."""
    return (
        json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False,
        ) + "\n"
    ).encode("utf-8")


class FrozenObligationPlanCompiler:
    """Reject policy changes and derive a fresh, detached plan on every call."""

    def __init__(self, contract_raw):
        _load_frozen_policy(contract_raw)
        self._contract_raw = contract_raw

    def compile(self):
        # Authenticate and parse again. A caller cannot change the policy by
        # mutating a returned plan or replacing the retained source bytes.
        policy = _load_frozen_policy(self._contract_raw)
        prefixes = policy["operation_schedule"]["prefixes"]

        def expand(name, active=()):
            if name in active:
                raise ValueError("lcer.operation_prefix_cycle")
            operations = []
            for item in prefixes[name]:
                if item in prefixes:
                    operations.extend(expand(item, (*active, name)))
                else:
                    operations.append(item)
            return operations

        families = {
            name: family
            for family in policy["failure_cases"]
            for name in family["runs"]
        }
        cases = {}
        for witness in policy["witnesses"]:
            name = witness["id"]
            cases[name] = {
                "id": name, "kind": "witness", "prefix": "P5",
                "witness": witness, "publication_count": 1,
                "terminal_canonical": "R1",
            }
        for program in policy["failure_programs"]:
            name = program["id"]
            family = families[name]
            cases[name] = {
                "id": name, "kind": "failure", "prefix": program["prefix"],
                "failure_program": program, "failure_family": family,
                "publication_count": int(family["boundary"] == "after_commit"),
                "terminal_canonical": family["canonical_remains"],
            }
        for index, point in enumerate(policy["canonical_faults"], 1):
            name = "C%02d" % index
            cases[name] = {
                "id": name, "kind": "canonical_fault", "prefix": "P2",
                "fault_point": point,
                "underlying_code": policy["canonical_fault_codes"][point],
                "publication_count": 0, "terminal_canonical": "R0",
            }

        if list(cases) != policy["artifact_hash_graph"]["case_ids"]:
            raise ValueError("lcer.case_inventory_mismatch")
        return {
            "schema": "city.live_evidence_obligation_plan.v1",
            "stage": "offline_contract_plan",
            "frozen_contract_sha256": FROZEN_CONTRACT_SHA256,
            # Keep every accepted field. Summaries never replace the policy.
            "constitutional_policy": policy,
            "frozen_case_plans": cases,
            "expanded_prefix_plans": {
                name: expand(name) for name in prefixes
            },
            "terminal_failure_plans": {
                program["id"]: {
                    "program": program, "family": families[program["id"]],
                }
                for program in policy["failure_programs"]
            },
            "case_evidence_plans": policy["artifact_hash_graph"]["case_record_targets"],
            "case_order": policy["artifact_hash_graph"]["case_ids"],
            "artifact_construction_order": policy["artifact_hash_graph"]["construction_order"],
            "typed_call_arguments": policy["call_trace_contract"]["dispatch"],
            "live_acceptance_verified": False,
        }

    def validate(self, plan):
        """Validate the complete plan against a new authenticated compilation."""
        supplied = _plan_bytes(plan)
        if supplied != _plan_bytes(self.compile()):
            raise ValueError("lcer.obligation_plan_mismatch")
        return hashlib.sha256(supplied).hexdigest()


def stored_json_bytes(value):
    """Serialize detached messages with sorted ASCII JSON and exactly one LF."""
    return _plan_bytes(value)


def parse_stored_json(raw):
    """Require one strict, canonically stored JSON object."""
    if type(raw) is not bytes:
        raise ValueError("lcer.schema_invalid")
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique_object,
            parse_constant=_reject_constants,
        )
        if type(value) is not dict or stored_json_bytes(value) != raw:
            raise ValueError("lcer.schema_invalid")
        return value
    except (ValueError, UnicodeError, TypeError, RecursionError) as error:
        raise ValueError("lcer.schema_invalid") from error


def _json_equal(left, right):
    if type(left) is bool or type(right) is bool:
        return type(left) is type(right) and left == right
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(
            _json_equal(left[key], right[key]) for key in left
        )
    if type(left) is list:
        return len(left) == len(right) and all(
            _json_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


class FrozenWireValidator:
    """Interpret only the vocabulary in the authenticated frozen schema bundle."""

    def __init__(self, contract_raw):
        _load_frozen_policy(contract_raw)
        self._contract_raw = contract_raw

    def validate(self, schema_name, value):
        definitions = _load_frozen_policy(self._contract_raw)["wire_schemas"]
        if schema_name not in definitions:
            raise ValueError("lcer.schema_invalid")

        def accepts(rule, item):
            if "$ref" in rule:
                reference = rule["$ref"]
                if not reference.startswith("#/$defs/"):
                    raise ValueError("lcer.schema_invalid")
                if not accepts(definitions[reference[len("#/$defs/"):]], item):
                    return False
            if "const" in rule and not _json_equal(item, rule["const"]):
                return False
            if "enum" in rule and not any(
                _json_equal(item, choice) for choice in rule["enum"]
            ):
                return False
            if "oneOf" in rule and sum(
                accepts(branch, item) for branch in rule["oneOf"]
            ) != 1:
                return False
            kind = rule.get("type")
            if kind == "object":
                if type(item) is not dict:
                    return False
                properties = rule["properties"]
                if not set(rule["required"]).issubset(item):
                    return False
                if rule["additionalProperties"] is False and not set(item).issubset(properties):
                    return False
                return all(accepts(properties[key], val) for key, val in item.items())
            if kind == "array":
                return type(item) is list and all(
                    accepts(rule["items"], entry) for entry in item
                )
            if kind == "string":
                return (type(item) is str and len(item) >= rule.get("minLength", 0)
                        and ("pattern" not in rule or re.search(rule["pattern"], item) is not None))
            if kind == "integer":
                integral = type(item) is int or (
                    type(item) is float and math.isfinite(item) and item.is_integer()
                )
                return (integral and item >= rule.get("minimum", -math.inf)
                        and item <= rule.get("maximum", math.inf))
            if kind == "boolean":
                return type(item) is bool
            if kind == "null":
                return item is None
            return kind is None

        try:
            valid = accepts(definitions[schema_name], value)
        except (KeyError, TypeError, ValueError, RecursionError) as error:
            raise ValueError("lcer.schema_invalid") from error
        if not valid:
            raise ValueError("lcer.schema_invalid")

    def parse(self, schema_name, raw):
        value = parse_stored_json(raw)
        self.validate(schema_name, value)
        return value


def select_frozen_case(contract_raw, case_id):
    """Select a complete frozen case; no caller-supplied policy override exists."""
    plan = FrozenObligationPlanCompiler(contract_raw).compile()
    if type(case_id) is not str or case_id not in plan["case_order"]:
        raise ValueError("lcer.case_not_frozen")
    return plan["frozen_case_plans"][case_id]
