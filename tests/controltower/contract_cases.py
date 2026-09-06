#!/usr/bin/env python3
"""Executable onboarding contract cases with isolated, observable faults."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('city_native', ROOT / 'tools/controltower/city_native.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def run(action, *extra):
    proc = subprocess.run(['./start.sh', action, '--json', *extra], cwd=ROOT, capture_output=True, text=True, timeout=360)
    return proc, json.loads(proc.stdout)


def receipt_fixture():
    ident = native.identity()
    digest = native.fingerprint(native.snapshot())
    return {'schema': 'controltower.native_repo_adapter_action_receipt.v1', 'repo': 'CITY',
            'action': 'city.verify-release', 'status': 'pass', 'returncode': 0,
            'changed_tracked_paths': [], 'source_mutations': 0, 'runtime_mutations': 0,
            'external_mutations': 0, 'target_mutations': 0, 'source_identity': ident,
            'observed_json': {'source_identity': ident, 'tracked_fingerprint': digest,
                              'verification_state': 'passed', 'verified_release_members': 172,
                              'claims': dict(native.CLAIMS)}}, ident, digest


def execute(case):
    before = native.snapshot()
    detail = {}
    if case == 'preservation':
        data = native.baseline()
        # Bind expected bytes to the original committed tree, independently of
        # the CLI's preservation verdict. LFS requires smudged historical bytes.
        names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', data['commit']], cwd=ROOT, text=True).splitlines()
        assert set(names) == set(data['files'])
        assert len(names) == 653
        locations = dict(data['files'])
        locations['References/Handover/handover-2026-08-30.md'] = locations.pop('handover.md')
        assert not native.check_files(locations)
        manifest = ROOT / data['release_manifest']
        members = {line[66:]: line[:64] for line in manifest.read_text().splitlines()}
        assert len(members) == 172 and not native.check_files(members)
        detail = {'baseline_files': len(names), 'release_members': len(members)}
    elif case == 'tampered-release':
        data = native.baseline()
        with tempfile.TemporaryDirectory(prefix='city-tamper-', dir='/private/tmp') as temp:
            fixture = Path(temp)
            (fixture / 'README.md').write_bytes((ROOT / 'README.md').read_bytes() + b'\nwrong\n')
            changed = native.check_files({'README.md': data['files']['README.md']}, fixture)
            assert changed == ['README.md']
            raise native.Refusal('CITY_RELEASE_CHANGED', changed)
    elif case == 'query-contract':
        outputs = {}
        for action in native.ACTIONS[:-1]:
            proc, value = run(action)
            assert proc.returncode == 0, value
            assert value['schema'] == 'city.native.v1' and value['status'] == 'pass'
            assert value['repo'] == 'CITY' and value['action'] == action
            assert value['source_identity'] == native.identity()
            assert value['claims'] == native.CLAIMS and value['failure_codes'] == []
            outputs[action] = value
        assert outputs['strategic-status']['phase_5'] == 'specification_review'
        assert outputs['strategic-status']['successor'] == 'Live Cross-Domain Evidence Round-Trip Proof'
        assert outputs['strategic-status']['implementation_authorized'] is False
        assert outputs['health']['health_state'] == 'degraded'
        assert outputs['health']['governance_state'] == 'ready'
        assert outputs['rollback-plan']['plan_only'] is True
        assert outputs['rollback-plan']['destructive_commands_executed'] == 0
        assert outputs['next-action']['argv'] == ['python3', '-B', native.SPEC_VALIDATOR, '--json']
        interface = json.loads((ROOT / '.controltower/interface.json').read_text())
        manifest = json.loads((ROOT / 'CONTROLTOWER_REPO.json').read_text())
        assert len(interface['commands']) == len(native.ACTIONS) == 6
        assert {tuple(c['argv']) for c in interface['commands']} == {tuple(c['argv']) for c in manifest['mount_contract']['actions']}
        for command in interface['commands']:
            assert command['argv'] == ['./start.sh', command['id'].removeprefix('city.'), '--json']
            assert command['mutability'] == 'read_only'
            assert command['requires_network'] is False and command['requires_credentials'] is False
            assert command['effects'] == {'source': 'none', 'runtime': 'none', 'evidence': 'receipt', 'external': 'none'}
        detail = {'native_families': 6, 'queries_executed': 5}
    elif case == 'release-execution':
        proc, value = run('verify-release')
        assert proc.returncode == 0, value
        assert value['verification_state'] == 'passed'
        assert value['verified_release_members'] == 172
        assert value['verifier_adversaries_rejected'] == 34
        assert value['changed_tracked_paths'] == []
        detail = {'verified_release_members': 172, 'verifier_adversaries_rejected': 34}
    elif case in ('unknown-action', 'extra-argument'):
        proc, value = run('erase-evidence' if case == 'unknown-action' else 'health', *([] if case == 'unknown-action' else ['--write']))
        expected = 'CITY_ACTION_UNKNOWN' if case == 'unknown-action' else 'CITY_ARGUMENTS_DENIED'
        assert proc.returncode == 2 and value['status'] == 'fail' and value['failure_codes'] == [expected]
        raise native.Refusal(expected, value['detail'])
    elif case == 'mutation-detected':
        with tempfile.TemporaryDirectory(prefix='city-isolation-', dir='/private/tmp') as temp:
            fixture = Path(temp) / 'source.txt'
            fixture.write_text('canonical')
            initial = {'source.txt': native.file_hash(fixture)}
            fixture.write_text('mutated')
            native.assert_unchanged(initial, {'source.txt': native.file_hash(fixture)})
    elif case in ('fresh-receipt', 'stale-receipt', 'forbidden-claim'):
        receipt, ident, digest = receipt_fixture()
        if case == 'stale-receipt':
            receipt['source_identity'] = {**ident, 'commit': '0' * 40}
        elif case == 'forbidden-claim':
            receipt['observed_json']['claims']['live_unreal_from_city'] = True
        assert native.current_receipt(receipt, ident, digest)
        detail = {'fixture_receipt_binding_passed': True, 'receipt_is_fixture': True}
    elif case == 'determinism':
        a, av = run('strategic-status')
        b, bv = run('strategic-status')
        assert a.returncode == b.returncode == 0 and a.stdout == b.stdout
        detail = {'identical_stdout_sha256': hashlib.sha256(a.stdout.encode()).hexdigest()}
    elif case == 'changed-input':
        receipt, ident, digest = receipt_fixture()
        with tempfile.TemporaryDirectory(prefix='city-input-', dir='/private/tmp') as temp:
            fixture = Path(temp) / 'input.json'
            fixture.write_text('{"state":1}')
            initial = native.fingerprint({'input.json': native.file_hash(fixture)})
            fixture.write_text('{"state":2}')
            changed = native.fingerprint({'input.json': native.file_hash(fixture)})
            assert changed != initial
            try:
                native.current_receipt(receipt, ident, changed)
            except native.Refusal as exc:
                assert exc.code == 'CITY_RECEIPT_STALE'
                raise native.Refusal('CITY_INPUT_CHANGED', {'before': initial, 'after': changed})
    elif case == 'references':
        refs = native.baseline()['references']
        assert len(refs) == 2 and not native.check_files(refs)
        detail = {'reference_files': refs}
    elif case == 'handover-current':
        text = (ROOT / 'handover.md').read_text()
        assert 'Phase 4 is sealed. Phase 5 is open for specification review only.' in text
        assert 'cd /Users/boandersson/Projects/CITY' in text
        assert '/Users/boandersson/Desktop' not in text
        assert 'The current work is Phase 3' not in text
        assert '## 20. Short return card' not in text
        assert all('./start.sh ' + action + ' --json' in text for action in native.ACTIONS)
        assert 'References/Git%20History/README.md' in text
        assert 'References/Handover/handover-2026-08-30.md' in text
        links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', text)
        assert links and all((ROOT / unquote(link)).is_file() for link in links)
        detail = {'local_links_verified': len(links), 'native_routes': 6, 'phase_4': 'sealed', 'phase_5': 'specification_review'}
    elif case == 'archive-integrity':
        data = native.baseline()
        expected = subprocess.check_output(['git', 'show', data['commit'] + ':handover.md'], cwd=ROOT)
        archive = ROOT / 'References/Handover/handover-2026-08-30.md'
        assert archive.read_bytes() == expected
        assert archive.read_bytes() != (ROOT / 'handover.md').read_bytes()
        assert native.ARCHIVED_ORIGINALS == {'handover.md': 'References/Handover/handover-2026-08-30.md'}
        assert (ROOT / 'tools/controltower/baseline.json').read_bytes() == subprocess.check_output(
            ['git', 'show', '1bf77c54b42db9dac2f26fcb6eac326664540ab7:tools/controltower/baseline.json'], cwd=ROOT)
        assert not native.check_original_files(data['files'])
        detail = {'original_handover_sha256': hashlib.sha256(expected).hexdigest(),
                  'originals_in_place': 652, 'originals_archived': 1, 'baseline_unchanged': True}
    elif case in ('archive-corrupt', 'archive-missing'):
        expected = {'handover.md': native.baseline()['files']['handover.md']}
        with tempfile.TemporaryDirectory(prefix='city-archive-fault-', dir='/private/tmp') as temp:
            fixture = Path(temp)
            # A valid original at the old path must not hide a missing or corrupt archive.
            (fixture / 'handover.md').write_bytes((ROOT / native.ARCHIVED_ORIGINALS['handover.md']).read_bytes())
            if case == 'archive-corrupt':
                archive = fixture / native.ARCHIVED_ORIGINALS['handover.md']
                archive.parent.mkdir(parents=True)
                archive.write_bytes((fixture / 'handover.md').read_bytes() + b'corrupt')
            changed = native.check_original_files(expected, fixture)
            assert changed == ['handover.md']
            raise native.Refusal('CITY_RELEASE_CHANGED', changed)
    elif case == 'history-audit':
        bundle = ROOT / 'References/Git History/THE_CITY-pre-LFS.bundle'
        assert native.file_hash(bundle) == '5dc6076cdcfeb880872e15adaca880b0f20255e28d1312b1597faac666ea1f0e'
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        with tempfile.TemporaryDirectory(prefix='city-original-history-', dir='/private/tmp') as temp:
            repository = Path(temp) / 'repo.git'
            cloned = subprocess.run(['git', 'clone', '--bare', str(bundle), str(repository)],
                                    capture_output=True, text=True, env=env, timeout=30)
            assert cloned.returncode == 0, cloned.stderr
            originals = {'bee3ecca660f884f3af727affae3ab1ceae2c401': '3302b4e34b412629776433a4b50b1b0a852e51ab',
                         '5d4eac983de281fcf7b03d78453e5f131204b946': 'e01411b0af3e819474d33e73432148585ec6a34c'}
            for commit, tree in originals.items():
                actual = subprocess.check_output(['git', '--git-dir=' + str(repository), 'rev-parse', commit + '^{tree}'],
                                                 text=True, env=env).strip()
                assert actual == tree
        detail = {'original_objects_verified': originals, 'network_access': False}
    elif case == 'successor-state':
        selected = native.load_selection()
        proc, state = run('strategic-status')
        assert proc.returncode == 0 and state['successor'] == selected['successor']
        assert state['phase_5'] == 'specification_review'
        assert state['implementation_authorized'] is False and state['specification_frozen'] is False
        assert native.SELECTION in native.snapshot() and native.SPEC_CONTRACT in native.snapshot()
        detail = {'selected': state['successor'], 'implementation_authorized': False}
    elif case.startswith('selection-'):
        with tempfile.TemporaryDirectory(prefix='city-selection-', dir='/private/tmp') as tmp:
            fixture = Path(tmp)
            for name in (native.SELECTION, native.SPECIFICATION, native.SPEC_CONTRACT):
                dest = fixture / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((ROOT / name).read_bytes())
            if case == 'selection-missing':
                (fixture / native.SELECTION).unlink()
            elif case == 'selection-tampered':
                (fixture / native.SPECIFICATION).write_text('Changed selected scope')
            elif case == 'selection-escalation':
                value = json.loads((fixture / native.SELECTION).read_text())
                value['implementation_authorized'] = True
                (fixture / native.SELECTION).write_text(json.dumps(value))
            else:
                raise AssertionError('Unknown selection case')
            native.load_selection(fixture)
            raise AssertionError('Bad selection accepted')
    elif case.startswith('spec-'):
        loaded = importlib.util.spec_from_file_location('city_spec', ROOT / native.SPEC_VALIDATOR)
        checker = importlib.util.module_from_spec(loaded)
        loaded.loader.exec_module(checker)
        contract = checker.parse((ROOT / native.SPEC_CONTRACT).read_text())
        if case in ('spec-contract', 'spec-self-test'):
            args = ['python3', '-B', native.SPEC_VALIDATOR, '--json']
            if case == 'spec-self-test':
                args.append('--self-test')
            proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=30)
            result = json.loads(proc.stdout)
            assert proc.returncode == 0 and result['status'] == 'pass', result
            assert result['unreal_executed'] is False and result['independent_review_accepted'] is False
            assert result['primary_witnesses'] == 8 and result['artifact_files'] == 219
            if case == 'spec-self-test':
                assert result['adversaries_rejected'] == 21 and result['schema_adversaries_rejected'] > 100
            detail = result
        else:
            if case == 'spec-witness-hole':
                contract['witnesses'].pop()
            elif case == 'spec-order':
                contract['scope']['canonical_order'] = ['arrival_time']
            elif case == 'spec-extra-field':
                contract['wire_schemas']['projection']['additionalProperties'] = True
            elif case == 'spec-failure':
                contract['failure_cases'][10]['canonical_remains'] = 'R0'
            elif case == 'spec-path':
                contract['planned_source_paths'][0] = '../escaped.py'
            elif case == 'spec-authority':
                contract['identity']['implementation_authorized'] = True
            else:
                raise AssertionError('Unknown spec case')
            try:
                checker.validate_contract(contract)
            except checker.InvalidSpec as exc:
                raise native.Refusal('CITY_SPEC_INVALID', str(exc)) from exc
            raise AssertionError('Invalid specification accepted')
    else:
        raise AssertionError('Unknown case: ' + case)
    native.assert_unchanged(before, native.snapshot())
    return detail


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', required=True)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    before = native.snapshot()
    try:
        detail = execute(args.case)
        result = {'status': 'pass', 'case': args.case, 'failure_codes': [], 'detail': detail}
        code = 0
    except native.Refusal as exc:
        result = {'status': 'rejected', 'case': args.case, 'failure_codes': [exc.code], 'detail': exc.detail}
        code = 2
    except Exception as exc:
        result = {'status': 'fail', 'case': args.case, 'failure_codes': ['CITY_CONTRACT_CASE_FAILED'], 'detail': str(exc)}
        code = 1
    native.assert_unchanged(before, native.snapshot())
    result['tracked_files_unchanged'] = True
    print(native.canonical(result), end='')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
