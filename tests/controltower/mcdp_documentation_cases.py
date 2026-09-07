"""Validate the CITY-owned P14 documentation and its bounded change surface."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

FROZEN_SHA='b862ceba039b1f2f418b01fe32221f14f095ce4894d163077b4eaa31dd0a8755'
BASE='5787612a4ecb78cc578a13d511649518009afb47'
DOCROOT='docs/mcdp/live-evidence-contract'
NAMES=['P14_DOCUMENTATION.md','SYSTEM_DESCRIPTION.md','OPERATOR_GUIDE.md','DESIGNER_GUIDE.md','WORKSHEET.md','FAILURE_HISTORY.md','VERSION_HISTORY.md','CONTRACT_LAWS.md']
SECTIONS={'SYSTEM_DESCRIPTION.md':['identity','scope','runtime','world_oracle','record_delivery'],
 'OPERATOR_GUIDE.md':['planned_commands','cost','launch_argv','launch_environment','build_argv'],
 'DESIGNER_GUIDE.md':['scope','exclusions','planned_source_paths','operation_schedule','process_input_contract'],
 'WORKSHEET.md':['witnesses','failure_programs','canonical_faults','checkpoints','artifact_relative_paths','release_members','release_manifest'],
 'FAILURE_HISTORY.md':['failure_execution_law','canonical_fault_codes','verifier_negative_cases'],
 'VERSION_HISTORY.md':['identity','review_gate']}
ALLOWED=[DOCROOT+'/'+n for n in NAMES]+['tests/controltower/mcdp_documentation_cases.py']
def need(ok,code):
    if not ok:raise ValueError(code)
def strict(raw):
    def pairs(rows):
        value={}
        for k,v in rows:need(k not in value,'CITY_DOC_DUPLICATE_KEY');value[k]=v
        return value
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'CITY_DOC_NONFINITE'))
def encode(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def block(raw):
    matches=re.findall(rb'```json\n(.*?)\n```',raw,re.S);need(len(matches)==1,'CITY_DOC_JSON_BLOCK');return matches[0]
def payload(c,name):return dict(schema='city.mcdp.documentation.v1',document=name,contract_sha256=FROZEN_SHA,projection={k:c[k] for k in SECTIONS[name]},live_acceptance_verified=False,game_implementation_authorized=False,game_sealed=False,trusted_ci=False)
def validate(docs,raw):
    need(sha(raw)==FROZEN_SHA,'CITY_DOC_SUBJECT');c=strict(raw)
    need(set(docs)==set(NAMES),'CITY_DOC_MISSING')
    names=re.findall(rb'^- `([^`/\\]+\.md)`$',docs[NAMES[0]],re.M)
    need([n.decode() for n in names]==NAMES,'CITY_DOC_MANIFEST')
    need(block(docs['CONTRACT_LAWS.md'])+b'\n'==raw,'CITY_DOC_LAWS')
    for name in SECTIONS:
        value=strict(block(docs[name]))
        need(all(value.get(k) is False for k in ['live_acceptance_verified','game_implementation_authorized','game_sealed','trusted_ci']),'CITY_DOC_AUTHORITY')
        need(value==payload(c,name),'CITY_DOC_PROJECTION')
    return dict(document_count=8,contract_field_count=len(c),document_root_sha256=sha(encode({n:sha(docs[n]) for n in NAMES})),live_acceptance_verified=False,game_implementation_authorized=False,game_sealed=False,trusted_ci=False)
def scope(paths):need(set(paths)<=set(ALLOWED) and len(set(paths))<=9,'CITY_DOC_SCOPE')
def run(root,case):
    raw=(root/'proof_kernel/live_cross_domain_evidence_round_trip_contract.json').read_bytes()
    docs={n:(root/DOCROOT/n).read_bytes() for n in NAMES};before={n:sha(v) for n,v in docs.items()};validate(docs,raw)
    if case=='scope-positive':
        def git(args):return subprocess.check_output(['git',*args],cwd=root,text=True).splitlines()
        paths=sorted(set(git(['diff','--name-only',BASE,'--'])+git(['ls-files','--others','--exclude-standard'])));scope(paths);return dict(changed_paths=paths,changed_file_count=len(paths),preserved_base_commit=BASE)
    if case=='scope-negative':scope(['proof_kernel/concurrent_external_evidence_arbitration.py'])
    elif case=='missing-doc':docs.pop('DESIGNER_GUIDE.md')
    elif case=='duplicate-manifest':docs[NAMES[0]]+=b'\n- `WORKSHEET.md`\n'
    elif case=='altered-law':docs['CONTRACT_LAWS.md']=docs['CONTRACT_LAWS.md'].replace(b'"fixed_candidate_set": true',b'"fixed_candidate_set": false',1)
    elif case in ['altered-projection','forbidden-claim','worksheet-omission']:
        name='WORKSHEET.md' if case=='worksheet-omission' else 'SYSTEM_DESCRIPTION.md';old=block(docs[name]);v=strict(old)
        if case=='forbidden-claim':v['game_sealed']=True
        elif case=='worksheet-omission':v['projection']['artifact_relative_paths'].pop()
        else:v['projection']['scope']['canonical_mutation_owner']='unreal'
        docs[name]=docs[name].replace(old,encode(v),1)
    elif case not in ['documents-positive','determinism-positive']:raise ValueError('CITY_DOC_CASE_UNKNOWN')
    result=validate(docs,raw)
    if case=='determinism-positive':need(result==validate(docs,raw),'CITY_DOC_DETERMINISM')
    need(before=={n:sha((root/DOCROOT/n).read_bytes()) for n in NAMES},'CITY_DOC_SOURCE_MUTATION')
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--json',action='store_true');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);a=p.parse_args()
    try:details=run(a.root.resolve(),a.case);v=dict(schema='city.mcdp.documentation_case.v1',status='pass',case=a.case,failure_codes=[],details=details);code=0
    except ValueError as exc:v=dict(schema='city.mcdp.documentation_case.v1',status='rejected',case=a.case,failure_codes=[str(exc)]);code=2
    print(json.dumps(v,sort_keys=True,separators=(',',':')));return code
if __name__=='__main__':raise SystemExit(main())
