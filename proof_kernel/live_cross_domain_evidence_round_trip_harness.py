"""Parent-owned canonical core for the frozen live evidence round trip.

Live acquisition orchestration is not yet implemented. This core consumes
supplied captures; it never generates physical Q evidence or claims a live run.
"""

import base64
import argparse
import hashlib
import os
from pathlib import Path

from live_cross_domain_evidence_round_trip import (
    FrozenObligationPlanCompiler,
    FrozenWireValidator,
    parse_stored_json,
    select_frozen_case,
    stored_json_bytes,
)


PROOF_ROOT = Path(__file__).resolve().parent


def _canonical_sequence(case):
    admission = "admit_external_input_candidate"
    construction = "construct_bext_from_sealed_fixture_set"
    resolution = "resolve_external_batch"
    order = case.get("witness", {}).get("presentation", ["domain_A", "domain_B"])
    complete = [(admission, domain) for domain in order] + [(construction, None), (resolution, None)]
    if case["kind"] != "failure":
        return complete
    name = case["id"]
    if name == "F01":
        return [(admission, "domain_A"), (construction, None)]
    if name in ("F02", "F03", "F05", "F06"):
        return [(admission, "domain_A")]
    if name in ("F04a", "F04b") or case["prefix"] == "P2":
        return complete[:3]
    if name in ("F10a", "F10b"):
        return complete + [(admission, "domain_A")]
    if case["prefix"] in ("P3", "P4", "P5"):
        return complete
    return []


def _read_bound_file(repo_root, relative_path, expected_sha256):
    path = repo_root / relative_path
    if (Path(relative_path).is_absolute() or ".." in Path(relative_path).parts
            or not path.resolve().is_relative_to(repo_root.resolve())
            or any(item.is_symlink() for item in [path, *path.parents])):
        raise ValueError("lcer.dependency_path_invalid")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("lcer.dependency_identity_mismatch")
    return raw


def _canonical_base64(encoded):
    if type(encoded) is not str:
        raise ValueError("lcer.schema_invalid")
    try:
        raw = base64.b64decode(encoded, validate=True)
        if base64.b64encode(raw).decode("ascii") != encoded:
            raise ValueError("lcer.schema_invalid")
        return raw
    except (ValueError, UnicodeError) as error:
        raise ValueError("lcer.schema_invalid") from error


def core_health(contract_raw, repo_root):
    policy = FrozenObligationPlanCompiler(contract_raw).compile()["constitutional_policy"]
    dependencies = {
        **policy["predecessors"], **policy["canonical_records"],
        **policy["unchanged_dependencies"],
    }
    identities = []
    for path, expected in sorted(dependencies.items()):
        raw = _read_bound_file(repo_root, path, expected)
        identities.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)})
    return {"scope": "preserved_core_dependencies", "files": identities,
            "live_execution_ready": False}


class CanonicalRoundTrip:
    """Invoke the unchanged predecessor and install its exact R1 at most once."""

    def __init__(self, contract_raw, case_id, proof_root=PROOF_ROOT):
        self._contract_raw = contract_raw
        self._case = select_frozen_case(contract_raw, case_id)
        self._validator = FrozenWireValidator(contract_raw)
        policy = FrozenObligationPlanCompiler(contract_raw).compile()["constitutional_policy"]
        repo_root = proof_root.parent
        self.health = core_health(contract_raw, repo_root)

        # Authenticate the entire preserved dependency set before importing the
        # only canonical implementation or its local serialization dependency.
        import concurrent_external_evidence_arbitration as canonical
        import kernel
        if (Path(canonical.__file__).resolve() != proof_root / "concurrent_external_evidence_arbitration.py"
                or Path(kernel.__file__).resolve() != proof_root / "kernel.py"):
            raise ValueError("lcer.dependency_identity_mismatch")
        self._canonical = canonical
        records = policy["canonical_records"]
        self._r0 = _read_bound_file(
            repo_root, "proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R0.json",
            records["proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R0.json"],
        )
        self._r1 = _read_bound_file(
            repo_root, "proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R1.json",
            records["proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R1.json"],
        )
        if canonical.stored_payload_bytes(canonical.initial_canonical_envelope()) != self._r0:
            raise ValueError("lcer.canonical_initial_mismatch")
        self._primary_fixture_raw = stored_json_bytes(canonical.primary_fixture(parse_stored_json(self._r0)))
        self._head_raw = self._r0
        self._published = None
        self._calls = []
        self._calls_sha256 = hashlib.sha256(b"").hexdigest()
        self._admitted = {}
        self._constructed = None
        self._sequence = _canonical_sequence(self._case)
        self._failed = False
        self._original_q = {}
        for domain, name in (("domain_A", "QA"), ("domain_B", "QB")):
            path = "proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_" + name + ".json"
            self._original_q[domain] = _read_bound_file(repo_root, path, records[path])

    @property
    def head_raw(self):
        return self._head_raw

    @property
    def publication_count(self):
        return int(self._published is not None)

    def retained_calls(self):
        return [parse_stored_json(raw) for raw in self._calls]

    def _check_admission_arguments(self, domain, supplied, q_object, q_bytes, materialization, emission):
        canonical = self._canonical
        original = parse_stored_json(self._original_q[domain])
        expected = parse_stored_json(self._original_q[domain])
        case = self._case["id"]
        if self._head_raw == self._r0 and case in ("F03", "F05", "F06"):
            if case == "F03":
                expected["target"]["id"] = "shared_slot_02"
            elif case == "F05":
                expected["source"]["source_record_hash"] = canonical.canonical_hash(parse_stored_json(self._r1))
            else:
                expected["proposed_effect"]["path"] = "/current_causal_state/forbidden_owner"
            expected["evidence"].pop("evidence_digest")
            expected["evidence"]["evidence_digest"] = canonical.evidence_digest(expected)
        if self._head_raw == self._r1 and case == "F10b":
            expected["input_id"] = "replay_probe_new_input"
        expected_raw = stored_json_bytes(expected)
        if case == "F02":
            expected_raw = expected_raw[:-1]
        if stored_json_bytes(q_object) != stored_json_bytes(expected) or q_bytes != expected_raw:
            raise ValueError("lcer.schema_invalid")
        process = materialization.get("process_instance_id")
        if type(process) is not str or not process or not process.isascii():
            raise ValueError("lcer.schema_invalid")
        r0 = parse_stored_json(self._r0)
        if (stored_json_bytes(materialization) != stored_json_bytes(canonical.materialization_acceptance_receipt(r0, domain, process)) or
                stored_json_bytes(emission) != stored_json_bytes(canonical.evidence_emission_receipt(r0, original, domain, process))):
            raise ValueError("lcer.schema_invalid")

    def call(self, function, arguments):
        policy = FrozenObligationPlanCompiler(self._contract_raw).compile()["constitutional_policy"]
        frozen_case = select_frozen_case(self._contract_raw, self._case["id"])
        if self._case != frozen_case:
            raise ValueError("lcer.case_configuration_mismatch")
        if self._sequence != _canonical_sequence(frozen_case):
            raise ValueError("lcer.case_configuration_mismatch")
        schema = policy["call_trace_contract"]["dispatch"].get(function)
        if schema is None:
            raise ValueError("lcer.canonical_function_not_declared")
        # Serialize and reparse so neither the caller nor a callee shares the
        # original argument objects with the retained trace.
        arguments_raw = stored_json_bytes(arguments)
        supplied = self._validator.parse(schema, arguments_raw)
        before_raw = self._head_raw
        if supplied["record_raw_utf8"].encode("utf-8") != before_raw:
            raise ValueError("lcer.stale_canonical_head")
        record = parse_stored_json(before_raw)
        canonical = self._canonical
        fault = supplied.get("fault_point") if function == "resolve_external_batch" else None
        if function == "resolve_external_batch" and fault != frozen_case.get("fault_point"):
            raise ValueError("lcer.case_fault_mismatch")
        index = len(self._calls)
        if self._failed or index >= len(self._sequence) or self._sequence[index][0] != function:
            raise ValueError("lcer.core_sequence_invalid")
        domain = self._sequence[index][1]
        result = None
        exception = None
        returned_raw = None
        published_raw = None

        if function == "admit_external_input_candidate":
            q_object = parse_stored_json(supplied["q_object_raw_utf8"].encode("utf-8"))
            q_bytes = _canonical_base64(supplied["q_raw_base64"])
            materialization = parse_stored_json(supplied["materialization_receipt_raw_utf8"].encode("utf-8"))
            emission = parse_stored_json(supplied["emission_receipt_raw_utf8"].encode("utf-8"))
            self._check_admission_arguments(domain, supplied, q_object, q_bytes, materialization, emission)
            positional = [record, q_object, q_bytes, materialization, emission]
            before_arguments = [stored_json_bytes(v) if type(v) is not bytes else v for v in positional]
            try:
                result = canonical.admit_external_input_candidate(record, q_object, q_bytes, materialization, emission)
            except (canonical.CanonicalEnvelopeRejected, canonical.ExternalEvidenceRejected,
                    canonical.RepresentationRejected) as error:
                exception = str(error)
            if before_arguments != [stored_json_bytes(v) if type(v) is not bytes else v for v in positional]:
                raise ValueError("lcer.canonical_argument_mutation")
            if exception is None:
                returned_raw = stored_json_bytes(result)
                self._admitted[domain] = returned_raw
        elif function == "construct_bext_from_sealed_fixture_set":
            fixture = parse_stored_json(supplied["fixture_raw_utf8"].encode("utf-8"))
            if stored_json_bytes(fixture) != self._primary_fixture_raw:
                raise ValueError("lcer.schema_invalid")
            presentation = [parse_stored_json(v.encode("utf-8")) for v in supplied["presentation_members_raw_utf8"]]
            order = frozen_case.get("witness", {}).get("presentation", ["domain_A", "domain_B"])
            if frozen_case["id"] == "F01":
                order = ["domain_A"]
            if frozen_case["id"] == "F04a":
                order = ["domain_A", "domain_A"]
            expected_members = [parse_stored_json(self._admitted[d]) for d in order]
            if frozen_case["id"] == "F04b":
                expected_members[1]["physical_event_id"] = expected_members[0]["physical_event_id"]
            if stored_json_bytes(presentation) != stored_json_bytes(expected_members):
                raise ValueError("lcer.schema_invalid")
            before_arguments = stored_json_bytes([record, fixture, presentation])
            try:
                result = canonical.construct_bext_from_sealed_fixture_set(record, fixture, presentation)
            except (canonical.CanonicalEnvelopeRejected, canonical.BatchConstructionRejected) as error:
                exception = str(error)
            if before_arguments != stored_json_bytes([record, fixture, presentation]):
                raise ValueError("lcer.canonical_argument_mutation")
            if exception is None:
                batch, members = result
                returned = {"bext_raw_utf8": stored_json_bytes(batch).decode("utf-8"),
                            "admitted_members": [{"input_id": name, "member_raw_utf8": stored_json_bytes(members[name]).decode("utf-8")}
                                                 for name in sorted(members)]}
                self._validator.validate("construction_return", returned)
                returned_raw = stored_json_bytes(returned)
                self._constructed = returned_raw
        else:
            batch = parse_stored_json(supplied["bext_raw_utf8"].encode("utf-8"))
            entries = supplied["admitted_members"]
            names = [entry["input_id"] for entry in entries]
            if names != sorted(set(names)):
                raise ValueError("lcer.schema_invalid")
            members = {entry["input_id"]: parse_stored_json(entry["member_raw_utf8"].encode("utf-8")) for entry in entries}
            constructed = {"bext_raw_utf8": supplied["bext_raw_utf8"], "admitted_members": entries}
            if self._constructed is None or stored_json_bytes(constructed) != self._constructed:
                raise ValueError("lcer.schema_invalid")
            before_arguments = stored_json_bytes([record, batch, members])
            try:
                result = canonical.resolve_external_batch(record, batch, members, fault_point=fault)
            except (canonical.CanonicalEnvelopeRejected, canonical.BatchResolutionRejected) as error:
                exception = str(error)
            if before_arguments != stored_json_bytes([record, batch, members]):
                raise ValueError("lcer.canonical_argument_mutation")
            if exception is None:
                returned_raw = canonical.stored_payload_bytes(result)
                if returned_raw != self._r1 or self._published is not None:
                    raise ValueError("lcer.canonical_publication_invalid")
                # This is the sole publication edge. No physical callback or
                # later display failure can roll it back.
                self._head_raw = returned_raw
                self._published = returned_raw
                published_raw = returned_raw

        trace = {
            "function": function, "record_before_raw_utf8": before_raw.decode("utf-8"),
            "return_raw_utf8": None if returned_raw is None else returned_raw.decode("utf-8"),
            "exception_code": exception, "record_after_raw_utf8": self._head_raw.decode("utf-8"),
            "published_record_raw_utf8": None if published_raw is None else published_raw.decode("utf-8"),
            "fault_point": fault, "arguments": supplied,
        }
        self._validator.validate("canonical_call", trace)
        trace_raw = stored_json_bytes(trace)
        self._calls.append(trace_raw)
        self._calls_sha256 = hashlib.sha256(self._calls_sha256.encode("ascii") + trace_raw).hexdigest()
        expected_exception = None
        if index == len(self._sequence) - 1:
            if frozen_case["kind"] == "canonical_fault":
                expected_exception = frozen_case["underlying_code"]
            elif frozen_case["kind"] == "failure":
                code = frozen_case["failure_program"]["underlying_code"]
                if code.startswith("concurrent_external_"):
                    expected_exception = code
        if exception != expected_exception:
            self._failed = True
            raise ValueError("lcer.unexpected_canonical_outcome")
        return result, trace

    def canonical_coverage(self):
        case = select_frozen_case(self._contract_raw, self._case["id"])
        if self._case != case or self._sequence != _canonical_sequence(case):
            raise ValueError("lcer.case_configuration_mismatch")
        observed_root = hashlib.sha256(b"").hexdigest()
        for raw in self._calls:
            observed_root = hashlib.sha256(observed_root.encode("ascii") + raw).hexdigest()
        if observed_root != self._calls_sha256:
            raise ValueError("lcer.core_trace_invalid")
        complete = (not self._failed and len(self._calls) == len(_canonical_sequence(case))
                    and self.publication_count == case["publication_count"]
                    and self._head_raw == (self._r1 if case["terminal_canonical"] == "R1" else self._r0))
        return {"expected_call_count": len(_canonical_sequence(case)), "observed_call_count": len(self._calls),
                "publication_count": self.publication_count, "canonical_prefix_complete": complete,
                "live_acceptance_verified": False}


class CoreRoundTripPipeline:
    """Execute and record the core stages. Physical acceptance stays unproved."""

    def __init__(self, contract_raw, case_id, proof_root=PROOF_ROOT):
        self._raw = contract_raw
        self._proof_root = proof_root
        self._case = select_frozen_case(contract_raw, case_id)
        self._stages = ["classify"]
        self._health = core_health(contract_raw, proof_root.parent)
        self._stages.append("health")
        compiler = FrozenObligationPlanCompiler(contract_raw)
        self._plan = compiler.compile()
        self._source_snapshot = {
            name: hashlib.sha256((proof_root.parent / name).read_bytes()).hexdigest()
            for name in self._plan["constitutional_policy"]["planned_source_paths"]
            if (proof_root.parent / name).exists()
        }
        self._stages.append("load_policy")
        self._plan_sha256 = compiler.validate(self._plan)
        self._core = CanonicalRoundTrip(contract_raw, case_id, proof_root)
        self._stages.append("check_constraints")
        self._finished = False

    @property
    def head_raw(self):
        return self._core.head_raw

    @property
    def publication_count(self):
        return self._core.publication_count

    def call(self, function, arguments):
        if self._finished:
            raise ValueError("lcer.core_sequence_invalid")
        return self._core.call(function, arguments)

    def finish(self, proof_path):
        if self._finished:
            raise ValueError("lcer.core_sequence_invalid")
        if self._stages != ["classify", "health", "load_policy", "check_constraints"]:
            raise ValueError("lcer.core_sequence_invalid")
        if self._case != select_frozen_case(self._raw, self._core._case["id"]):
            raise ValueError("lcer.case_configuration_mismatch")
        if FrozenObligationPlanCompiler(self._raw).validate(self._plan) != self._plan_sha256:
            raise ValueError("lcer.obligation_plan_mismatch")
        health = core_health(self._raw, self._proof_root.parent)
        if health != self._health:
            raise ValueError("lcer.dependency_identity_mismatch")
        coverage = self._core.canonical_coverage()
        if not coverage["canonical_prefix_complete"]:
            raise ValueError("lcer.core_coverage_incomplete")
        destination = Path(proof_path)
        if (not destination.is_absolute() or destination.exists() or
                destination.resolve().is_relative_to(self._proof_root.parent.resolve()) or
                any(p.is_symlink() for p in [destination, *destination.parents])):
            raise ValueError("lcer.core_proof_path_invalid")
        sources = {}
        for name in self._plan["constitutional_policy"]["planned_source_paths"]:
            path = self._proof_root.parent / name
            if path.exists():
                sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if sources != self._source_snapshot:
            raise ValueError("lcer.core_source_changed")
        proof = {"schema": "city.live_evidence_core_proof.v1", "case_id": self._case["id"],
                 "contract_sha256": hashlib.sha256(self._raw).hexdigest(),
                 "plan_sha256": self._plan_sha256, "source_files": sources,
                 "stages": [*self._stages, "assess_coverage", "record_proof"],
                 "health": health, "canonical_calls": self._core.retained_calls(),
                 "coverage": coverage, "canonical_head_raw_utf8": self.head_raw.decode("utf-8"),
                 "live_acceptance_verified": False, "full_implementation_verified": False}
        raw = stored_json_bytes(proof)
        with destination.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if destination.read_bytes() != raw:
            raise ValueError("lcer.core_proof_write_invalid")
        self._finished = True
        return {"schema": "city.live_evidence_core_eligibility.v1", "case_id": self._case["id"],
                "stage": "gate_eligibility", "canonical_prefix_eligible": True,
                "proof_path": str(destination), "proof_sha256": hashlib.sha256(raw).hexdigest(),
                "live_acceptance_verified": False, "full_implementation_verified": False}


def main():
    parser = argparse.ArgumentParser(description="Frozen live evidence acquisition")
    routes = parser.add_subparsers(dest="command", required=True)
    acquire = routes.add_parser("acquire")
    acquire.add_argument("--runtime-parent", required=True)
    acquire.add_argument("--output", required=True)
    parser.parse_args()
    parser.error("live acquisition is not implemented; core API evidence grants no live acceptance")


if __name__ == "__main__":
    main()
