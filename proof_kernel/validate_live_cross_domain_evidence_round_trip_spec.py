#!/usr/bin/env python3
"""Review-only specification checks. Never launch Unreal or authorize a seal."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = 'proof_kernel/live_cross_domain_evidence_round_trip_contract.json'
SECTION_DIGESTS = {'schema': 'd8512edc744d2c6d1bfc4dd39f7feec230c7b2e36a64c6968bbbd203759a0c06', 'identity': '7661f7194293fc4e50bb342c53eaff48b77d2c759d6d665561564d808a215b02', 'predecessors': 'ab3398e0f0dcc39d338338c45eb659df5e7d6bad294d966d8bab803dd95546c8', 'canonical_records': 'e4077d944a9cb0208f758ef5311f88d52cc90696e6dfebee03ff2b096d7da625', 'scope': 'bd6e7d4eca6dc2928eaa128751d0bfd9cd1f5da696c50846b799df8acfcb13ba', 'exclusions': '797b148684709a1a8de33c95b247e84b2bb5fa2ae4d76b7aea37feb082f6f22f', 'witnesses': '7f1a275abec8a59d19048c6aec020f181dd369d0cd60183ce83fc4b076e0e4c6', 'checkpoints': 'e3bfc88f90e1efc273b8691255f99ae10cae45818e3cea54e8e542727c11788b', 'failure_cases': '1c78f094a6fbfffed910b33aa6dc17665e5031c30941e19ece4e4b4a3617eb25', 'canonical_faults': 'aa1993fca2d222d89631756ed79528dff219d2725a1d36dd6b89759bfac3019e', 'process_binding_fields': 'fa3c0246ca767dce0094a7be1172fd578a6a419087053a504a6d455c7d7b78c0', 'observation_fields': 'e111a7bab06de0396f61c21f570222463b8d0a8c3e4732b6d5b20fee98d3ac29', 'evidence_fields': '8788a6e0a3e77ad8732b909267bb05ffce4d0ea8aa8d24e442110c1af5690d8e', 'output_fields': 'fee8d8bf7704022195cd4f33daec06f94105ebc329a4090c1c2260c1d37bd176', 'runtime': 'db961f59ee8e1ec7ba28d4aa9cb5d132c7942e1d8f64a326e0ae4092bdf5c7e4', 'planned_commands': '10a86f7729b299a141aa24dd683dfe33a0b24b1c7a9951b642058d5aa7fbf53a', 'planned_source_paths': 'e436a8acbbbcf069e3731bf352d1521a6a9a352aa4443a276940e4cb45825b9e', 'cost': '07870f560ae666194f8c2a527659991ba90f811d5ae0b18b00baf3996c9db745', 'review_gate': '44791b6166a77f10e00ef95e6cf00035ca043b5f585b53aa35c9601167a18df0', 'wire_schemas': '3c03c004988cbab0c10329aad6093f8355004bbdf14cc2345edbef19aa0746a1', 'command_contract': '9715ba851c8a10e98ce22753ab2f4dc854d2d71ac5e487db3774b794a3ec1adf', 'launch_argv': '578f42e35057fc2956633f665fe031f2bd606ecc53708bd1109664fb55ffb60a', 'launch_environment': 'ffdde5e6670ccbf3ae5ba79097d11b5a858361c057154874a8e346be9e40bfb0', 'descriptor_contract': '15dbd3949e4cb5c4ea24b8b07476e727c28b4ad18bdf5a8bb9bb9263ec21c6b2', 'build_argv': 'a578bbc6352f628da74b2ac6cea2d319c63b337e075afc967f0bc8afa764cc1f', 'plugin_contract': 'f8b86348dc63ad3101eeef8054b85fc4c1def7f264b61bab3e2682302f1d012f', 'artifact_relative_paths': '77d88a5327abf8e64a0e4bb7a4dc04194aa6a681cf100a396460020428f83eaf', 'artifact_record_contract': 'ccfb531d3556c118b9e785f812576885a573766b8f5689159e003407356a4838', 'release_members': '1ae49d12af72d67943f0bfd0422efd7b2b25dc4d0ede3ebb836b6fd9e838d041', 'release_manifest': '77ccf37a54abef6f35b7536359f1878176349e1f5f5734dbfcf36d87b6299b03', 'schema_contract': '451bdd37a806c8a959f50b8c44349709bf8a590071cb6415dd22a71f189afb90', 'record_delivery': 'd6035238221146e62758a21d89e02163a1cad90f1d2403ac2389f29eb6192011', 'world_oracle': 'c7dc47130aa179c795288eb1a429c6a9f69f2abb23c4e2a6830f5a9b780d9a07', 'operation_schedule': '57531f926a4bd030d2bea9e3e8495aea698389d54fb539d02b3cc7bb5fcf1ce0', 'failure_programs': 'a5d67b87dcce5b0c4429c62ca0af2c08f96066110481adf30930eb8109e41994', 'failure_execution_law': '33dcea3499c38b7c5a8c5b7d4a116cff193e423fd897a179093b102646db28c5', 'unchanged_dependencies': 'cea13dc6ff9c640f5d745e8e8690b58cabcd982e0b21aaf59403bbfe5ea58627', 'dependency_contract': '6ebc3820c54fb520737c296edf42ce3693ac5d0230f551e4a9806d589ec68c6f', 'process_input_contract': '33b9a61bc6b70e7c3105cd44bd6b703ca5712169241c22be15d3bda1b51ab60e', 'artifact_hash_graph': '8f9f9899313a8f3b7b527f6cece92d9a803405a6469a5fec429d069568362131', 'verifier_negative_cases': '10d298d1ba38789ed40995d73ecef5de482ddf82794e88de0068a388e181640c'}

class InvalidSpec(ValueError):
    pass

def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidSpec('duplicate JSON key: ' + key)
        result[key] = value
    return result

def parse(raw):
    return json.loads(raw, object_pairs_hook=no_duplicates,
                      parse_constant=lambda value: (_ for _ in ()).throw(InvalidSpec('non-finite number')))

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()

def schema_checks(value, adversaries=False):
    """Check real JSON Schema closure and bad records, independent of digests.

    Examples exercise shape only. They are never physical/canonical evidence.
    """
    definitions = value['wire_schemas']
    def walk(schema):
        if '$ref' in schema:
            name = schema['$ref'].removeprefix('#/$defs/')
            if schema['$ref'] != '#/$defs/' + name or name not in definitions:
                raise InvalidSpec('unresolved or external schema reference')
        if schema.get('type') == 'object':
            if schema.get('additionalProperties') is not False or set(schema.get('required', [])) != set(schema.get('properties', {})):
                raise InvalidSpec('open or optional object field set')
            for child in schema['properties'].values():
                walk(child)
        if 'items' in schema:
            walk(schema['items'])
        for child in schema.get('oneOf', []):
            walk(child)
    def sample(schema):
        if '$ref' in schema:
            return sample(definitions[schema['$ref'].split('/')[-1]])
        if 'const' in schema:
            return copy.deepcopy(schema['const'])
        if 'enum' in schema:
            return copy.deepcopy(schema['enum'][0])
        if 'oneOf' in schema:
            return sample(schema['oneOf'][0])
        kind = schema['type']
        if kind == 'object':
            return {k:sample(v) for k,v in schema['properties'].items()}
        if kind == 'array':
            return [sample(schema['items'])]
        if kind == 'string':
            return '0'*64 if 'pattern' in schema else 'example'
        if kind == 'integer':
            return schema.get('minimum', 0)
        if kind == 'boolean':
            return False
        if kind == 'null':
            return None
        raise InvalidSpec('unhandled example schema type')
    rejected = []
    for name, schema in definitions.items():
        walk(schema)
        bundle = {'$schema':'https://json-schema.org/draft/2020-12/schema',
                  '$defs':definitions, '$ref':'#/$defs/'+name}
        Draft202012Validator.check_schema(bundle)
        validator = Draft202012Validator(bundle)
        example = sample(schema)
        if list(validator.iter_errors(example)):
            raise InvalidSpec('no valid structural example: '+name)
        if adversaries:
            missing = copy.deepcopy(example); missing.pop(next(iter(missing)))
            extra = copy.deepcopy(example); extra['undeclared_field'] = True
            for label, bad in [('missing',missing),('extra',extra),('wrong_type',[])]:
                if not list(validator.iter_errors(bad)):
                    raise InvalidSpec('malformed schema object accepted: '+name+'/'+label)
                rejected.append(name+'/'+label)
    return {'schema_count':len(definitions), 'schema_adversaries_rejected':len(rejected),
            'schema_examples_class':'structural_only_not_runtime_records'}

def graph_checks(value):
    paths = value['artifact_relative_paths']
    graph = value['artifact_hash_graph']
    if len(paths) != len(set(paths)) or set(graph['acquisition_targets']) != set(paths)-{'acquisition.json'}:
        raise InvalidSpec('acquisition index is not exact and self-excluding')
    for case, targets in graph['case_record_targets'].items():
        expected = {p for p in paths if p.startswith(case+'/') and p != case+'/record.json'}
        if set(targets) != expected or len(targets) != len(expected):
            raise InvalidSpec('case index graph differs')
    if len(graph['case_ids']) != value['cost']['total_pair_runs_per_acquisition']:
        raise InvalidSpec('case budget differs')
    if len(paths) != value['cost']['artifact_files'] or len(value['release_members']) != value['cost']['release_members_excluding_manifest']:
        raise InvalidSpec('artifact/release budget differs')
    if not set(value['unchanged_dependencies']).issubset(value['release_members']):
        raise InvalidSpec('unbound executable dependency')

def validate_contract(value, root=ROOT):
    errors = []
    if not isinstance(value, dict) or set(value) != set(SECTION_DIGESTS):
        raise InvalidSpec('contract top-level field set differs')
    for section, expected in SECTION_DIGESTS.items():
        if digest(value[section]) != expected:
            errors.append('closed contract section differs: ' + section)
    # Structural commitments are not a claim of independent semantic acceptance.
    if errors:
        raise InvalidSpec('; '.join(errors))
    orders = [('domain_A', 'domain_B'), ('domain_B', 'domain_A')]
    observed = [(tuple(w['emission']), tuple(w['presentation']), tuple(w['refresh'])) for w in value['witnesses']]
    if observed != list(itertools.product(orders, repeat=3)):
        raise InvalidSpec('full three-order witness product required')
    paths = value['planned_source_paths'] + value['release_members']
    for name in paths:
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or not name or str(p) != name:
            raise InvalidSpec('unsafe relative path')
        if not (root / p).resolve().is_relative_to(root.resolve()):
            raise InvalidSpec('path escapes owning repository')
    for name, expected in {**value['predecessors'], **value['canonical_records'], **value['unchanged_dependencies']}.items():
        p = root / name
        if p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise InvalidSpec('predecessor bytes differ: ' + name)
    schema_result = schema_checks(value)
    graph_checks(value)
    return {**schema_result, 'section_count': len(SECTION_DIGESTS), 'primary_witnesses': 8,
            'failure_cases': len(value['failure_cases']), 'canonical_fault_cases': 6,
            'artifact_files': len(value['artifact_relative_paths']),
            'release_members': len(value['release_members']),
            'validation_class': 'document_structure_only', 'implementation_authorized': False,
            'independent_review_accepted': False, 'unreal_executed': False}

def self_test(value):
    mutations = {}
    v=copy.deepcopy(value);v['witnesses'].pop();mutations['missing_witness']=v
    v=copy.deepcopy(value);v['scope']['canonical_order'].reverse();mutations['arrival_order']=v
    v=copy.deepcopy(value);v['scope']['extra_authority']=True;mutations['nested_extra_field']=v
    v=copy.deepcopy(value);v['failure_cases'][10]['canonical_remains']='R0';mutations['rollback_after_commit']=v
    v=copy.deepcopy(value);v['planned_source_paths'][0]='../escape.py';mutations['path_escape']=v
    v=copy.deepcopy(value);v['identity']['implementation_authorized']=True;mutations['authority_escalation']=v
    v=copy.deepcopy(value);v['runtime']['timeout_effect']='drop_candidate';mutations['timeout_membership']=v
    v=copy.deepcopy(value);v['wire_schemas']['projection']['additionalProperties']=True;mutations['projection_extra_fields']=v
    v=copy.deepcopy(value);v['release_members'].pop();mutations['release_subset']=v
    v=copy.deepcopy(value);v['process_binding_fields'].remove('macos_birth_tuple');mutations['pid_only_identity']=v
    v=copy.deepcopy(value);v['cost']['total_pair_runs_per_acquisition']=8;mutations['underpriced_controls']=v
    v=copy.deepcopy(value);v['plugin_contract']['existing_source_edits']=True;mutations['sealed_source_edit']=v
    v=copy.deepcopy(value);v['record_delivery']['channel']='projection_only';mutations['missing_raw_R0']=v
    v=copy.deepcopy(value);del v['wire_schemas']['response'];mutations['missing_response_schema']=v
    v=copy.deepcopy(value);del v['wire_schemas']['actor_row']['properties']['generation'];mutations['aggregate_only_oracle']=v
    v=copy.deepcopy(value);del v['failure_programs'][0]['stage'];mutations['unbound_fault_stage']=v
    v=copy.deepcopy(value);del v['process_input_contract']['cwd'];mutations['unbound_cwd']=v
    v=copy.deepcopy(value);del v['unchanged_dependencies']['proof_kernel/kernel.py'];mutations['unbound_serializer']=v
    v=copy.deepcopy(value);v['artifact_hash_graph']['acquisition_targets'].append('acquisition.json');mutations['acquisition_self_hash']=v
    rejected=[]
    for name, variant in mutations.items():
        try:
            validate_contract(variant)
        except InvalidSpec:
            rejected.append(name)
        else:
            raise InvalidSpec('mutation accepted: ' + name)
    for raw in ('{"a":{"b":1,"b":2}}','{"a":NaN}'):
        try:
            parse(raw)
        except (ValueError, InvalidSpec):
            rejected.append('duplicate_key' if '"b"' in raw else 'nonfinite_number')
        else:
            raise InvalidSpec('malformed JSON accepted')
    return {'adversaries_rejected':len(rejected),'adversaries':rejected,
            **schema_checks(value, adversaries=True)}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--json',action='store_true')
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    try:
        spec=importlib.util.spec_from_file_location('city_native', ROOT/'tools/controltower/city_native.py')
        native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
        native.load_selection()
        value=parse((ROOT/CONTRACT).read_text())
        result=validate_contract(value)
        if args.self_test: result.update(self_test(value))
        result.update(schema='city.specification_validation.v1',status='pass',failure_codes=[])
        print(json.dumps(result,sort_keys=True));return 0
    except Exception as exc:
        print(json.dumps({'schema':'city.specification_validation.v1','status':'fail',
                          'failure_codes':['CITY_SPEC_INVALID'],'detail':str(exc),
                          'unreal_executed':False,'implementation_authorized':False},sort_keys=True));return 2
if __name__=='__main__':
    raise SystemExit(main())
