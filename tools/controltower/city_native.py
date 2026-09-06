#!/usr/bin/env python3
"""CITY's bounded ControlTower interface. Historical proof files are read-only."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / 'tools/controltower/baseline.json'
SCHEMA = 'city.native.v1'
ACTIONS = ('strategic-status', 'health', 'next-action', 'rollback-plan', 'validation-state', 'verify-release')
CLAIMS = {'live_unreal_from_city': False, 'phase_5_authorized': False,
          'production_ready': False, 'trusted_ci': False, 'new_game_seal': False}


class Refusal(Exception):
    def __init__(self, code, detail):
        self.code, self.detail = code, detail
        super().__init__(detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n'


def file_hash(path):
    if path.is_symlink() or not path.is_file():
        raise Refusal('CITY_FILE_UNSAFE', str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else path.name)
    with path.open('rb') as handle:
        digest = hashlib.sha256()
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
        return digest.hexdigest()


def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, check=False)
    if result.returncode:
        raise Refusal('CITY_GIT_FAILED', args[0])
    return result.stdout.decode('utf-8')


def identity():
    return {'commit': git('rev-parse', 'HEAD').strip(), 'tree': git('rev-parse', 'HEAD^{tree}').strip()}


def snapshot():
    paths = set(git('ls-files', '-z').split('\0')) - {''}
    # Include new governance code during candidate validation, before the first commit.
    for folder in ('tools/controltower', 'tests/controltower'):
        paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT / folder).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts)
    return {p: file_hash(ROOT / p) if (ROOT / p).exists() else 'missing' for p in sorted(paths)}


def fingerprint(files):
    return hashlib.sha256(canonical(files).encode()).hexdigest()


def baseline():
    return json.loads(BASELINE.read_text())


def check_files(expected, root=ROOT):
    changed = []
    for path, digest in expected.items():
        try:
            okay = file_hash(root / path) == digest
        except Refusal:
            okay = False
        if not okay:
            changed.append(path)
    return changed


def preserved():
    data = baseline()
    changed = check_files(data['files'])
    if changed:
        raise Refusal('CITY_RELEASE_CHANGED', changed)
    return data


def assert_claims(claims):
    if claims != CLAIMS:
        raise Refusal('CITY_CLAIM_FORBIDDEN', 'Onboarding grants no additional game or trusted execution claims.')


def assert_unchanged(before, after):
    changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
    if changed:
        raise Refusal('CITY_READ_ONLY_VIOLATION', changed)


def current_receipt(receipt, current_identity, current_fingerprint):
    if (receipt.get('schema') != 'controltower.native_repo_adapter_action_receipt.v1'
            or receipt.get('repo') != 'CITY' or receipt.get('action') != 'city.verify-release'
            or receipt.get('status') != 'pass' or receipt.get('returncode') != 0
            or receipt.get('changed_tracked_paths') != []
            or any(receipt.get(k) != 0 for k in ('source_mutations', 'runtime_mutations', 'external_mutations', 'target_mutations'))
            or any(receipt.get('source_identity', {}).get(k) != v for k, v in current_identity.items())
            or receipt.get('observed_json', {}).get('source_identity') != current_identity
            or receipt.get('observed_json', {}).get('tracked_fingerprint') != current_fingerprint
            or receipt.get('observed_json', {}).get('verification_state') != 'passed'
            or receipt.get('observed_json', {}).get('verified_release_members') != 172):
        raise Refusal('CITY_RECEIPT_STALE', 'Receipt is missing, failed, or belongs to different files or Git identity.')
    assert_claims(receipt['observed_json'].get('claims'))
    return True


def validation_state(current_identity, files):
    path = ROOT / '.controltower/receipts/native-city-verify-release.json'
    if not path.is_file():
        return {'validation_state': 'not_run_at_current_head', 'receipt_path': path.relative_to(ROOT).as_posix()}
    try:
        current_receipt(json.loads(path.read_text()), current_identity, fingerprint(files))
    except (Refusal, ValueError):
        return {'validation_state': 'stale_or_invalid', 'receipt_path': path.relative_to(ROOT).as_posix()}
    return {'validation_state': 'passed_at_current_head', 'receipt_path': path.relative_to(ROOT).as_posix(),
            'evidence_class': 'local_development', 'receipt_sha256': file_hash(path)}


def verify_release():
    before = snapshot()
    command = [sys.executable, '-B', 'proof_kernel/verify_cross_domain_canonical_occupancy_materialization_release.py', 'verify']
    # The frozen verifier has historical absolute Unreal commitments. It verifies
    # stored evidence; it neither rebuilds nor launches Unreal from this checkout.
    with tempfile.TemporaryDirectory(prefix='city-release-', dir='/private/tmp') as temporary:
        env = {k: v for k, v in os.environ.items() if not k.startswith('PYTHON')}
        env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPYCACHEPREFIX=temporary + '/pycache',
                   PYTHONPATH=str(ROOT / 'proof_kernel'), TMPDIR=temporary)
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=300)
        except subprocess.TimeoutExpired:
            assert_unchanged(before, snapshot())
            raise Refusal('CITY_VERIFIER_TIMEOUT', 'Frozen release verifier exceeded 300 seconds.')
    assert_unchanged(before, snapshot())
    expected = 'verified 172/172 release members; verifier adversaries 34/34 rejected;'
    if result.returncode != 0 or expected not in result.stdout:
        raise Refusal('CITY_VERIFIER_FAILED', {'returncode': result.returncode, 'stderr_tail': result.stderr[-2000:], 'stdout_tail': result.stdout[-1000:]})
    return {'verification_state': 'passed', 'verified_release_members': 172,
            'verifier_adversaries_rejected': 34, 'command': command,
            'stdout_sha256': hashlib.sha256(result.stdout.encode()).hexdigest(),
            'stderr_sha256': hashlib.sha256(result.stderr.encode()).hexdigest(),
            'tracked_fingerprint': fingerprint(before), 'changed_tracked_paths': [],
            'verifier_note': 'Frozen output retains pre-seal wording. The later sealed evidence record remains authoritative.'}


def answer(action):
    data = preserved()
    current = identity()
    files = snapshot()
    result = {'schema': SCHEMA, 'status': 'pass', 'repo': 'CITY', 'action': action,
              'source_identity': current, 'claims': CLAIMS, 'failure_codes': []}
    if action == 'strategic-status':
        result.update(active_proof='Cross-Domain Canonical Occupancy Materialization Proof v0.1.0',
                      continuation='0.7.0-draft.83', capacity='0.1.11', phase_5='closed',
                      successor='not_selected', authority='canonical_python_records',
                      development_checkout=str(ROOT), reference_checkout='/Users/boandersson/Desktop/Games/THE_CITY',
                      source_documents=['THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md',
                                        'Co-op Open-City FPS Simulation - v0.7 Working Continuation.md'])
    elif action == 'health':
        refs_changed = check_files(data['references'])
        interface = json.loads((ROOT / '.controltower/interface.json').read_text())
        expected_ids = {'city.' + name for name in ACTIONS}
        command_ids = [item['id'] for item in interface['commands']]
        valid_interface = len(command_ids) == len(expected_ids) and set(command_ids) == expected_ids
        governance = all((ROOT / p).is_file() for p in ('AGENTS.md', 'SwedeVO.md', 'CONTROLTOWER_REPO.json', 'RUNTIME_MANIFEST.md'))
        if refs_changed or not valid_interface or not governance:
            raise Refusal('CITY_GOVERNANCE_INVALID', {'reference_changes': refs_changed, 'interface_valid': valid_interface, 'governance_present': governance})
        result.update(health_state='degraded', governance_state='ready', sealed_files='intact',
                      verified_baseline_files=len(data['files']), release_member_count=172,
                      limits=['Live Unreal execution from CITY has not been acquired.'],
                      **validation_state(current, files))
    elif action == 'next-action':
        result.update(next_action='verify_sealed_release', argv=['./start.sh', 'verify-release', '--json'],
                      controltower_argv=['../ControlTower', 'repo', 'CITY', 'run', 'city.verify-release', '--approve', '--json'],
                      future_work='Select and authorize a successor through MCDP before game implementation.',
                      phase_5='closed')
    elif action == 'rollback-plan':
        result.update(plan_only=True, baseline_commit=data['commit'], baseline_tree=data['tree'],
                      steps=['Save current work and inspect Git status.',
                             'Use a separate checkout of the baseline commit to inspect the original state.',
                             'Revert only reviewed onboarding commits if removal is authorized.',
                             'Refresh or demount CITY through Projects-root ControlTower after an identity change.'],
                      history_bundle='References/Git History/THE_CITY-pre-LFS.bundle',
                      destructive_commands_executed=0)
    elif action == 'validation-state':
        result.update(**validation_state(current, files))
    elif action == 'verify-release':
        result.update(**verify_release())
    assert_claims(result['claims'])
    return result


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    aliases = {'--status': 'strategic-status', '--validate': 'health'}
    try:
        action = aliases.get(args[0], args[0]) if args else 'strategic-status'
        if action not in ACTIONS:
            raise Refusal('CITY_ACTION_UNKNOWN', action)
        if args and args[1:] not in ([], ['--json']):
            raise Refusal('CITY_ARGUMENTS_DENIED', args[1:])
        payload = answer(action)
        print(canonical(payload), end='')
        return 0
    except (Refusal, OSError, ValueError, KeyError) as exc:
        code = exc.code if isinstance(exc, Refusal) else 'CITY_INPUT_INVALID'
        detail = exc.detail if isinstance(exc, Refusal) else str(exc)
        print(canonical({'schema': SCHEMA, 'status': 'fail', 'repo': 'CITY', 'failure_codes': [code], 'detail': detail}), end='')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
