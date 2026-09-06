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

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = 'proof_kernel/live_cross_domain_evidence_round_trip_contract.json'
SECTION_DIGESTS = {'schema': 'd8512edc744d2c6d1bfc4dd39f7feec230c7b2e36a64c6968bbbd203759a0c06', 'identity': '70a9e191cc3c2616a5193230fd0a957b5ded5a6327b9e6b565e9587dbbadf287', 'predecessors': 'ab3398e0f0dcc39d338338c45eb659df5e7d6bad294d966d8bab803dd95546c8', 'canonical_records': 'e4077d944a9cb0208f758ef5311f88d52cc90696e6dfebee03ff2b096d7da625', 'scope': 'bd6e7d4eca6dc2928eaa128751d0bfd9cd1f5da696c50846b799df8acfcb13ba', 'exclusions': '797b148684709a1a8de33c95b247e84b2bb5fa2ae4d76b7aea37feb082f6f22f', 'witnesses': '7f1a275abec8a59d19048c6aec020f181dd369d0cd60183ce83fc4b076e0e4c6', 'checkpoints': 'e3bfc88f90e1efc273b8691255f99ae10cae45818e3cea54e8e542727c11788b', 'failure_cases': '15c0c9c3ff9a62b1098b6f4d37d96cd6903a4422fcbf84e1cd76ee79e651f89a', 'canonical_faults': 'aa1993fca2d222d89631756ed79528dff219d2725a1d36dd6b89759bfac3019e', 'process_binding_fields': '206940af992a165e7fe50ea035c009c81cda5c41a85d95a308c1a337236f1eb7', 'observation_fields': 'a06896183dd45c796b21bd81dbd4045889256b04dabf2df7bd740f19032d1749', 'evidence_fields': '8788a6e0a3e77ad8732b909267bb05ffce4d0ea8aa8d24e442110c1af5690d8e', 'output_fields': 'fee8d8bf7704022195cd4f33daec06f94105ebc329a4090c1c2260c1d37bd176', 'runtime': '781440f6e59cd4a3f20cf5552a43826665c3af28f462b2c9c1f43e73bd61b9bc', 'planned_commands': '10a86f7729b299a141aa24dd683dfe33a0b24b1c7a9951b642058d5aa7fbf53a', 'planned_source_paths': 'e436a8acbbbcf069e3731bf352d1521a6a9a352aa4443a276940e4cb45825b9e', 'cost': '167f2074b82f2c03bf5434c019649a933771b55936c6f921be4a7adeca3dfd53', 'review_gate': '44791b6166a77f10e00ef95e6cf00035ca043b5f585b53aa35c9601167a18df0', 'wire_schemas': '5b9f2e1380e3ab48f772ee5de13b0c31b3c61af75f79cda31727e5451a67645d', 'command_contract': '0bf26ea7dee3ab8c4d8bf71d96a96112710ede077e5dcaaabdd621f7bb1336da', 'launch_argv': '578f42e35057fc2956633f665fe031f2bd606ecc53708bd1109664fb55ffb60a', 'launch_environment': 'ffdde5e6670ccbf3ae5ba79097d11b5a858361c057154874a8e346be9e40bfb0', 'descriptor_contract': '15dbd3949e4cb5c4ea24b8b07476e727c28b4ad18bdf5a8bb9bb9263ec21c6b2', 'build_argv': 'ae3b89f4d881501102beda2a69fe81b89f4a1daa144cec71d2c0c87aa1eea315', 'plugin_contract': 'f8b86348dc63ad3101eeef8054b85fc4c1def7f264b61bab3e2682302f1d012f', 'artifact_relative_paths': 'd1fe0b0d7d2ac892655e0d2b2bffcd2ac6730b1404b411bb327d1f9a372659ef', 'artifact_record_contract': '2f9f6bcc4536bb06795c14f20b1ff0fe463c7da044a593e92c683ba9ee923364', 'release_members': '76e882bb5fa26e1222d8beff9fee41e309ad8fb09ae1dc8e9310476ed6b26b27', 'release_manifest': '77ccf37a54abef6f35b7536359f1878176349e1f5f5734dbfcf36d87b6299b03'}

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
    for name, expected in {**value['predecessors'], **value['canonical_records']}.items():
        p = root / name
        if p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise InvalidSpec('predecessor bytes differ: ' + name)
    return {'section_count': len(SECTION_DIGESTS), 'primary_witnesses': 8,
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
    return {'adversaries_rejected':len(rejected),'adversaries':rejected}

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
