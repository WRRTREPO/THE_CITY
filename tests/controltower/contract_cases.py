#!/usr/bin/env python3
"""Executable onboarding contract cases with isolated, observable faults."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

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
        assert not native.check_files(data['files'])
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
        assert outputs['strategic-status']['phase_5'] == 'closed'
        assert outputs['strategic-status']['successor'] == 'not_selected'
        assert outputs['health']['health_state'] == 'degraded'
        assert outputs['health']['governance_state'] == 'ready'
        assert outputs['rollback-plan']['plan_only'] is True
        assert outputs['rollback-plan']['destructive_commands_executed'] == 0
        assert outputs['next-action']['argv'] == ['./start.sh', 'verify-release', '--json']
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
