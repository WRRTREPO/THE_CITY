"""Current PR1 core tests. Full live-release acceptance is still outstanding."""

import copy
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from live_cross_domain_evidence_round_trip import (
    FrozenObligationPlanCompiler,
    FrozenWireValidator,
    parse_stored_json,
    select_frozen_case,
    stored_json_bytes,
)
from live_cross_domain_evidence_round_trip_harness import CanonicalRoundTrip, CoreRoundTripPipeline, core_health


CONTRACT_PATH = Path(__file__).with_name("live_cross_domain_evidence_round_trip_contract.json")


def schema_example(schema, definitions):
    if "$ref" in schema:
        return schema_example(definitions[schema["$ref"].split("/")[-1]], definitions)
    if "const" in schema:
        return copy.deepcopy(schema["const"])
    if "enum" in schema:
        return copy.deepcopy(schema["enum"][0])
    if "oneOf" in schema:
        return schema_example(schema["oneOf"][0], definitions)
    kind = schema["type"]
    if kind == "object":
        return {key: schema_example(value, definitions) for key, value in schema["properties"].items()}
    if kind == "array":
        return [schema_example(schema["items"], definitions)]
    if kind == "string":
        return "0" * 64 if "pattern" in schema else "example"
    if kind == "integer":
        return schema.get("minimum", 0)
    if kind == "boolean":
        return False
    if kind == "null":
        return None
    raise AssertionError("Unhandled frozen schema type: " + kind)


class FrozenCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = CONTRACT_PATH.read_bytes()
        cls.policy = json.loads(cls.raw)

    def test_complete_policy_and_case_inventory(self):
        plan = FrozenObligationPlanCompiler(self.raw).compile()
        self.assertEqual(plan["constitutional_policy"], self.policy)
        self.assertEqual(len(plan["constitutional_policy"]), 43)
        self.assertEqual(plan["case_order"], self.policy["artifact_hash_graph"]["case_ids"])
        self.assertEqual(len(plan["frozen_case_plans"]), 35)
        self.assertEqual(len(plan["terminal_failure_plans"]), 21)
        self.assertEqual(len(plan["expanded_prefix_plans"]), 6)
        self.assertFalse(plan["live_acceptance_verified"])

    def test_every_policy_term_is_binding(self):
        compiler = FrozenObligationPlanCompiler(self.raw)
        for key in self.policy:
            with self.subTest(term=key):
                plan = compiler.compile()
                plan["constitutional_policy"][key] = None
                with self.assertRaisesRegex(ValueError, "^lcer.obligation_plan_mismatch$"):
                    compiler.validate(plan)

    def test_subject_and_output_mutation_cannot_replace_policy(self):
        compiler = FrozenObligationPlanCompiler(self.raw)
        original = compiler.compile()
        digest = compiler.validate(original)
        poisoned = compiler.compile()
        poisoned["constitutional_policy"].clear()
        poisoned["frozen_case_plans"].clear()
        self.assertEqual(compiler.compile(), original)
        self.assertEqual(compiler.validate(compiler.compile()), digest)
        compiler._contract_raw = self.raw + b" "
        with self.assertRaisesRegex(ValueError, "^lcer.frozen_contract_mismatch$"):
            compiler.compile()
        with self.assertRaisesRegex(ValueError, "^lcer.contract_bytes_required$"):
            FrozenObligationPlanCompiler(bytearray(self.raw))

    def test_selector_cannot_add_or_edit_cases(self):
        for name in self.policy["artifact_hash_graph"]["case_ids"]:
            self.assertEqual(select_frozen_case(self.raw, name)["id"], name)
        for name in ["W9", "F19", "C07", "w1", "", None, ["W1"]]:
            with self.subTest(case=name):
                with self.assertRaisesRegex(ValueError, "^lcer.case_not_frozen$"):
                    select_frozen_case(self.raw, name)

    def test_exact_stored_json_boundary(self):
        value = {"name": "caf\u00e9", "nested": {"ready": True}}
        raw = b'{"name":"caf\\u00e9","nested":{"ready":true}}\n'
        self.assertEqual(stored_json_bytes(value), raw)
        self.assertEqual(parse_stored_json(raw), value)
        invalid = [raw[:-1], raw + b"\n", b" " + raw, raw + b"{}\n",
                   b'{"name":"caf\xc3\xa9","nested":{"ready":true}}\n',
                   b'{"n":{"x":1,"x":1}}\n', b'{"n":NaN}\n',
                   b'{"n":Infinity}\n', b'{"n":1e999}\n', b'[]\n',
                   b'{"n":"\xff"}\n']
        for candidate in invalid:
            with self.subTest(raw=candidate):
                with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
                    parse_stored_json(candidate)

    def test_every_frozen_wire_schema(self):
        validator = FrozenWireValidator(self.raw)
        definitions = self.policy["wire_schemas"]
        self.assertEqual(len(definitions), 49)
        for name, schema in definitions.items():
            base = schema_example(schema, definitions)
            with self.subTest(schema=name, case="positive"):
                self.assertEqual(validator.parse(name, stored_json_bytes(base)), base)
            missing = copy.deepcopy(base)
            del missing[schema["required"][0]]
            extra = dict(base, unlisted=True)
            key = schema["required"][0]
            duplicate = (b"{" + json.dumps(key).encode() + b":"
                         + stored_json_bytes(base[key]).rstrip(b"\n") + b","
                         + stored_json_bytes(base)[1:])
            for kind, raw in [("missing", stored_json_bytes(missing)),
                              ("extra", stored_json_bytes(extra)),
                              ("type", b"[]\n"), ("duplicate", duplicate)]:
                with self.subTest(schema=name, case=kind):
                    with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
                        validator.parse(name, raw)

    def test_boolean_numeric_and_string_boundaries(self):
        validator = FrozenWireValidator(self.raw)
        definitions = self.policy["wire_schemas"]
        projection = schema_example(definitions["projection"], definitions)
        for bad in [True, False, 2, -1, 0.5]:
            with self.subTest(generation=bad):
                with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
                    validator.validate("projection", dict(projection, generation=bad))
        artifact = {"path": "evidence.json", "sha256": "a" * 64, "size_bytes": 0}
        validator.validate("artifact_hash", dict(artifact, size_bytes=1.0))
        for field, bad in [("size_bytes", True), ("size_bytes", -1),
                           ("size_bytes", 0.5), ("size_bytes", float("inf")),
                           ("path", ""), ("sha256", "a" * 63), ("sha256", "G" * 64)]:
            with self.subTest(field=field, value=bad):
                with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
                    validator.validate("artifact_hash", dict(artifact, **{field: bad}))

    def test_nested_reference_and_oneof_rejection(self):
        validator = FrozenWireValidator(self.raw)
        definitions = self.policy["wire_schemas"]
        command = schema_example(definitions["command"], definitions)
        command["payload"] = schema_example(definitions["process_binding"], definitions)
        validator.validate("command", command)
        del command["payload"]["macos_birth_tuple"]["microseconds"]
        with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
            validator.validate("command", command)
        command["payload"] = {}
        with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
            validator.validate("command", command)
        validator._contract_raw = self.raw + b" "
        with self.assertRaisesRegex(ValueError, "^lcer.frozen_contract_mismatch$"):
            validator.validate("command", command)


class CanonicalCoreTests(unittest.TestCase):
    """Synthetic receipts test Python calls only. They are never live evidence."""

    @classmethod
    def setUpClass(cls):
        cls.raw = CONTRACT_PATH.read_bytes()
        cls.policy = json.loads(cls.raw)

    def new_core(self, case):
        core = CanonicalRoundTrip(self.raw, case)
        import concurrent_external_evidence_arbitration as canonical
        return core, canonical

    def admission(self, core, canonical, domain, q=None, q_bytes=None):
        r0 = canonical.initial_canonical_envelope()
        original = canonical.external_evidence_q(r0, domain)
        supplied = original if q is None else q
        process = "unit_test_" + domain
        args = {
            "schema": "city.live_evidence_admission_arguments.v1",
            "record_raw_utf8": core.head_raw.decode("utf-8"),
            "q_object_raw_utf8": stored_json_bytes(supplied).decode("utf-8"),
            "q_raw_base64": base64.b64encode(canonical.stored_q_bytes(supplied) if q_bytes is None else q_bytes).decode("ascii"),
            "materialization_receipt_raw_utf8": canonical.stored_receipt_bytes(canonical.materialization_acceptance_receipt(r0, domain, process)).decode("utf-8"),
            "emission_receipt_raw_utf8": canonical.stored_receipt_bytes(canonical.evidence_emission_receipt(r0, original, domain, process)).decode("utf-8"),
        }
        return core.call("admit_external_input_candidate", args)

    def prepare_batch(self, core, canonical, admission_order, presentation_order):
        admitted = {}
        for domain in admission_order:
            value, trace = self.admission(core, canonical, domain)
            self.assertIsNone(trace["exception_code"])
            self.assertIsNone(trace["published_record_raw_utf8"])
            admitted[domain] = value
        args = {
            "schema": "city.live_evidence_construction_arguments.v1",
            "record_raw_utf8": core.head_raw.decode("utf-8"),
            "fixture_raw_utf8": stored_json_bytes(canonical.primary_fixture()).decode("utf-8"),
            "presentation_members_raw_utf8": [stored_json_bytes(admitted[d]).decode("utf-8") for d in presentation_order],
        }
        value, trace = core.call("construct_bext_from_sealed_fixture_set", args)
        return value, trace

    def resolution_args(self, core, batch, mapping, fault=None):
        return {
            "schema": "city.live_evidence_resolution_arguments.v1",
            "record_raw_utf8": core.head_raw.decode("utf-8"),
            "bext_raw_utf8": stored_json_bytes(batch).decode("utf-8"),
            "admitted_members": [{"input_id": name, "member_raw_utf8": stored_json_bytes(mapping[name]).decode("utf-8")} for name in sorted(mapping)],
            "fault_point": fault,
        }

    def test_canonical_order_variants_publish_exact_r1_once(self):
        for witness in self.policy["witnesses"][::2]:
            with self.subTest(witness=witness["id"]):
                core, canonical = self.new_core(witness["id"])
                before = core.head_raw
                pair, trace = self.prepare_batch(core, canonical, witness["presentation"], witness["presentation"])
                self.assertIsNone(trace["exception_code"])
                args = self.resolution_args(core, *pair)
                original_args = copy.deepcopy(args)
                result, trace = core.call("resolve_external_batch", args)
                self.assertEqual(args, original_args)
                self.assertIsNone(trace["exception_code"])
                self.assertEqual(trace["record_before_raw_utf8"].encode(), before)
                expected = CONTRACT_PATH.parent / "ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R1.json"
                self.assertEqual(canonical.stored_payload_bytes(result), expected.read_bytes())
                self.assertEqual(core.head_raw, expected.read_bytes())
                self.assertEqual(trace["published_record_raw_utf8"].encode(), expected.read_bytes())
                self.assertEqual(core.publication_count, 1)
                with self.assertRaisesRegex(ValueError, "^lcer.stale_canonical_head$"):
                    core.call("resolve_external_batch", original_args)
                self.assertEqual(core.publication_count, 1)

    def test_six_actual_resolver_faults_preserve_r0(self):
        domains = ["domain_A", "domain_B"]
        for index, point in enumerate(self.policy["canonical_faults"], 1):
            with self.subTest(fault=point):
                core, canonical = self.new_core("C%02d" % index)
                before = core.head_raw
                pair, trace = self.prepare_batch(core, canonical, domains, domains)
                self.assertIsNone(trace["exception_code"])
                result, trace = core.call("resolve_external_batch", self.resolution_args(core, *pair, fault=point))
                self.assertIsNone(result)
                self.assertEqual(trace["exception_code"], self.policy["canonical_fault_codes"][point])
                self.assertIsNone(trace["return_raw_utf8"])
                self.assertIsNone(trace["published_record_raw_utf8"])
                self.assertEqual(core.head_raw, before)
                self.assertEqual(core.publication_count, 0)

    def test_incomplete_candidate_set_never_publishes(self):
        core, canonical = self.new_core("F01")
        before = core.head_raw
        pair, trace = self.prepare_batch(core, canonical, ["domain_A"], ["domain_A"])
        self.assertIsNone(pair)
        expected = next(p["underlying_code"] for p in self.policy["failure_programs"] if p["id"] == "F01")
        self.assertEqual(trace["exception_code"], expected)
        self.assertEqual(core.head_raw, before)
        self.assertEqual(core.publication_count, 0)

    def test_only_exact_primary_fixture_is_accepted(self):
        for selected in ("qa_only_fixture", "qb_only_fixture", "unlisted_field"):
            with self.subTest(fixture=selected):
                core, canonical = self.new_core("F01")
                member, _ = self.admission(core, canonical, "domain_A")
                fixture = (canonical.qa_only_fixture() if selected == "qa_only_fixture"
                           else canonical.qb_only_fixture() if selected == "qb_only_fixture"
                           else {**canonical.primary_fixture(), "unlisted": True})
                args = {
                    "schema": "city.live_evidence_construction_arguments.v1",
                    "record_raw_utf8": core.head_raw.decode("utf-8"),
                    "fixture_raw_utf8": stored_json_bytes(fixture).decode("utf-8"),
                    "presentation_members_raw_utf8": [stored_json_bytes(member).decode("utf-8")],
                }
                before = core.head_raw
                with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
                    core.call("construct_bext_from_sealed_fixture_set", args)
                self.assertEqual(core.head_raw, before)
                self.assertEqual(core.publication_count, 0)

    def test_unknown_or_incomplete_harness_argv_rejects(self):
        import subprocess
        import sys
        harness = CONTRACT_PATH.parent / "live_cross_domain_evidence_round_trip_harness.py"
        for args in ([], ["health"], ["acquire"], ["acquire", "--override"]):
            with self.subTest(args=args):
                result = subprocess.run([sys.executable, "-B", str(harness), *args],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(result.stderr)

    def test_raw_q_bytes_reach_the_actual_admission_call(self):
        core, canonical = self.new_core("F02")
        q = canonical.external_evidence_q(canonical.initial_canonical_envelope(), "domain_A")
        malformed = canonical.stored_q_bytes(q)[:-1]
        result, trace = self.admission(core, canonical, "domain_A", q_bytes=malformed)
        expected = next(p["underlying_code"] for p in self.policy["failure_programs"] if p["id"] == "F02")
        self.assertEqual(trace["exception_code"], expected)
        self.assertEqual(base64.b64decode(trace["arguments"]["q_raw_base64"]), malformed)
        self.assertIsNone(result)
        self.assertEqual(core.publication_count, 0)

    def test_replay_failures_do_not_undo_publication(self):
        domains = ["domain_A", "domain_B"]
        for case in ["F10a", "F10b"]:
            with self.subTest(case=case):
                core, canonical = self.new_core(case)
                pair, _ = self.prepare_batch(core, canonical, domains, domains)
                _, trace = core.call("resolve_external_batch", self.resolution_args(core, *pair))
                self.assertIsNone(trace["exception_code"])
                before = core.head_raw
                q = canonical.external_evidence_q(canonical.initial_canonical_envelope(), "domain_A")
                if case == "F10b":
                    q["input_id"] = "replay_probe_new_input"
                result, trace = self.admission(core, canonical, "domain_A", q=q)
                expected = next(p["underlying_code"] for p in self.policy["failure_programs"] if p["id"] == case)
                self.assertEqual(trace["exception_code"], expected)
                self.assertIsNone(result)
                self.assertEqual(core.head_raw, before)
                self.assertEqual(core.publication_count, 1)

    def test_typed_call_rejects_unknown_arguments_and_functions(self):
        core, _ = self.new_core("W1")
        before = core.head_raw
        with self.assertRaisesRegex(ValueError, "^lcer.canonical_function_not_declared$"):
            core.call("arbitrary_function", {})
        with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
            core.call("admit_external_input_candidate", {"unlisted": True})
        self.assertEqual(core.head_raw, before)
        self.assertEqual(core.publication_count, 0)

    def test_frozen_case_cannot_select_another_fault(self):
        core, canonical = self.new_core("W1")
        domains = ["domain_A", "domain_B"]
        pair, _ = self.prepare_batch(core, canonical, domains, domains)
        args = self.resolution_args(core, *pair, fault=self.policy["canonical_faults"][0])
        with self.assertRaisesRegex(ValueError, "^lcer.case_fault_mismatch$"):
            core.call("resolve_external_batch", args)
        self.assertEqual(core.publication_count, 0)
        core._case["publication_count"] = 0
        with self.assertRaisesRegex(ValueError, "^lcer.case_configuration_mismatch$"):
            core.call("resolve_external_batch", self.resolution_args(core, *pair))


class CorePipelineTests(unittest.TestCase):
    admission = CanonicalCoreTests.admission
    prepare_batch = CanonicalCoreTests.prepare_batch
    resolution_args = CanonicalCoreTests.resolution_args

    @classmethod
    def setUpClass(cls):
        cls.raw = CONTRACT_PATH.read_bytes()
        cls.policy = json.loads(cls.raw)

    def make(self, case):
        pipeline = CoreRoundTripPipeline(self.raw, case)
        import concurrent_external_evidence_arbitration as canonical
        return pipeline, canonical

    def test_four_order_variants_record_core_proof_before_eligibility(self):
        with tempfile.TemporaryDirectory(prefix="city-core-proof-", dir="/private/tmp") as directory:
            for witness in self.policy["witnesses"][::2]:
                with self.subTest(case=witness["id"]):
                    pipeline, canonical = self.make(witness["id"])
                    pair, _ = self.prepare_batch(pipeline, canonical, witness["presentation"], witness["presentation"])
                    pipeline.call("resolve_external_batch", self.resolution_args(pipeline, *pair))
                    path = Path(directory) / (witness["id"] + ".json")
                    result = pipeline.finish(path)
                    self.assertTrue(result["canonical_prefix_eligible"])
                    self.assertFalse(result["live_acceptance_verified"])
                    self.assertFalse(result["full_implementation_verified"])
                    raw = path.read_bytes()
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), result["proof_sha256"])
                    proof = parse_stored_json(raw)
                    self.assertEqual(proof["stages"], ["classify", "health", "load_policy", "check_constraints",
                                                       "assess_coverage", "record_proof"])
                    self.assertEqual(result["stage"], "gate_eligibility")
                    self.assertEqual(len(proof["canonical_calls"]), 4)
                    self.assertEqual(proof["coverage"]["publication_count"], 1)
                    self.assertEqual(proof["canonical_head_raw_utf8"].encode(), pipeline.head_raw)
                    with self.assertRaisesRegex(ValueError, "^lcer.core_sequence_invalid$"):
                        pipeline.finish(Path(directory) / "second.json")

    def test_six_faults_and_incomplete_set_produce_actual_failure_trace_proofs(self):
        with tempfile.TemporaryDirectory(prefix="city-core-fault-", dir="/private/tmp") as directory:
            for index, fault in enumerate(self.policy["canonical_faults"], 1):
                case = "C%02d" % index
                pipeline, canonical = self.make(case)
                pair, _ = self.prepare_batch(pipeline, canonical, ["domain_A", "domain_B"], ["domain_A", "domain_B"])
                pipeline.call("resolve_external_batch", self.resolution_args(pipeline, *pair, fault=fault))
                path = Path(directory) / (case + ".json")
                pipeline.finish(path)
                proof = parse_stored_json(path.read_bytes())
                self.assertEqual(proof["canonical_calls"][-1]["exception_code"], self.policy["canonical_fault_codes"][fault])
                self.assertEqual(proof["coverage"]["publication_count"], 0)
            pipeline, canonical = self.make("F01")
            self.prepare_batch(pipeline, canonical, ["domain_A"], ["domain_A"])
            path = Path(directory) / "F01.json"
            pipeline.finish(path)
            self.assertEqual(parse_stored_json(path.read_bytes())["coverage"]["observed_call_count"], 2)

    def test_missing_stages_or_calls_cannot_write_eligibility(self):
        with tempfile.TemporaryDirectory(prefix="city-core-missing-", dir="/private/tmp") as directory:
            path = Path(directory) / "proof.json"
            pipeline, _ = self.make("W1")
            with self.assertRaisesRegex(ValueError, "^lcer.core_coverage_incomplete$"):
                pipeline.finish(path)
            self.assertFalse(path.exists())
            pipeline._stages.remove("health")
            with self.assertRaisesRegex(ValueError, "^lcer.core_sequence_invalid$"):
                pipeline.finish(path)
            self.assertFalse(path.exists())

    def test_skipped_admission_changed_member_and_changed_bext_reject(self):
        pipeline, canonical = self.make("W1")
        member, _ = self.admission(pipeline, canonical, "domain_A")
        args = {"schema": "city.live_evidence_construction_arguments.v1",
                "record_raw_utf8": pipeline.head_raw.decode(),
                "fixture_raw_utf8": stored_json_bytes(canonical.primary_fixture()).decode(),
                "presentation_members_raw_utf8": [stored_json_bytes(member).decode()]}
        with self.assertRaisesRegex(ValueError, "^lcer.core_sequence_invalid$"):
            pipeline.call("construct_bext_from_sealed_fixture_set", args)
        peer, _ = self.admission(pipeline, canonical, "domain_B")
        changed = copy.deepcopy(member); changed["unlisted"] = True
        args["presentation_members_raw_utf8"] = [stored_json_bytes(changed).decode(), stored_json_bytes(peer).decode()]
        with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
            pipeline.call("construct_bext_from_sealed_fixture_set", args)
        args["presentation_members_raw_utf8"][0] = stored_json_bytes(member).decode()
        pair, _ = pipeline.call("construct_bext_from_sealed_fixture_set", args)
        resolution = self.resolution_args(pipeline, *pair)
        changed = json.loads(resolution["bext_raw_utf8"]); changed["unlisted"] = True
        resolution["bext_raw_utf8"] = stored_json_bytes(changed).decode()
        with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
            pipeline.call("resolve_external_batch", resolution)
        self.assertEqual(pipeline.publication_count, 0)

    def test_forged_retained_trace_cannot_supply_coverage(self):
        pipeline, canonical = self.make("W1")
        self.admission(pipeline, canonical, "domain_A")
        altered = pipeline._core.retained_calls()[0]
        altered["return_raw_utf8"] = "{}\n"
        pipeline._core._calls[0] = stored_json_bytes(altered)
        with tempfile.TemporaryDirectory(prefix="city-core-tamper-", dir="/private/tmp") as directory:
            path = Path(directory) / "proof.json"
            with self.assertRaisesRegex(ValueError, "^lcer.core_trace_invalid$"):
                pipeline.finish(path)
            self.assertFalse(path.exists())

    def test_health_authenticates_actual_preserved_files_and_rejects_drift(self):
        health = core_health(self.raw, CONTRACT_PATH.parent.parent)
        self.assertFalse(health["live_execution_ready"])
        for row in health["files"]:
            raw = (CONTRACT_PATH.parent.parent / row["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
            self.assertEqual(len(raw), row["size_bytes"])
        with tempfile.TemporaryDirectory(prefix="city-core-health-", dir="/private/tmp") as directory:
            path = Path(directory) / health["files"][0]["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"changed preserved dependency")
            with self.assertRaisesRegex(ValueError, "^lcer.dependency_identity_mismatch$"):
                core_health(self.raw, Path(directory))


if __name__ == "__main__":
    unittest.main()
