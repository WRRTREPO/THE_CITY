"""Parent-owned acquisition components for the frozen live evidence round trip.

The public route stays closed until source audit, native input derivation and
complete release construction are connected. Capture fixtures confer no live
acceptance; the real canonical core never fabricates physical Q evidence.
"""

import sys

_STDLIB_DIRECTORY = (getattr(sys, '_stdlib_dir', None) or sys.base_prefix +
                     '/lib/python%d.%d' % sys.version_info[:2])
_STDLIB_PATHS = (_STDLIB_DIRECTORY, _STDLIB_DIRECTORY + '/lib-dynload',
                 _STDLIB_DIRECTORY.rsplit('/', 1)[0] + '/python%d%d.zip' % sys.version_info[:2])
sys.path[:] = _STDLIB_PATHS
sys.dont_write_bytecode = True
sys.pycache_prefix = None

import base64
import argparse
from collections import Counter, deque
import ctypes
import errno
import hashlib
import json
import math
import os
from pathlib import Path
import pwd
import re
import select
import signal
import stat
import struct
import subprocess
import sysconfig
import threading
import time

PROOF_ROOT = Path(__file__).absolute().parent


def _prepare_source_imports():
    """Close alternate module paths before the first candidate dependency."""
    if PROOF_ROOT != PROOF_ROOT.resolve() or any(path.is_symlink() for path in [PROOF_ROOT, *PROOF_ROOT.parents]):
        raise ValueError('lcer.dependency_path_invalid')
    standard = set(sys.builtin_module_names)
    library = Path(sysconfig.get_path('stdlib'))
    standard.update(path.stem for path in library.glob('*.py'))
    standard.update(path.name for path in library.iterdir() if path.is_dir() and (path / '__init__.py').is_file())
    extensions = Path(sysconfig.get_config_var('DESTSHARED') or library / 'lib-dynload')
    if extensions.is_dir():
        standard.update(path.name.split('.')[0] for path in extensions.iterdir()
                        if path.is_file() and path.suffix in ('.so', '.dylib'))
    local = {'live_cross_domain_evidence_round_trip', 'live_cross_domain_evidence_round_trip_harness',
             'verify_live_cross_domain_evidence_round_trip_release', 'test_live_cross_domain_evidence_round_trip',
             'concurrent_external_evidence_arbitration', 'kernel'}
    for path in PROOF_ROOT.rglob('*'):
        if path.is_symlink():
            raise ValueError('lcer.dependency_path_invalid')
        if (path.is_file() and path.suffix in ('.pyc', '.pyo', '.so', '.dylib')) or (
                path.parent == PROOF_ROOT and ((path.suffix == '.py' and path.stem in standard)
                                              or (path.is_dir() and path.name in standard | local))):
            raise ValueError('lcer.source_input_forbidden')
    for name in local:
        loaded = sys.modules.get(name)
        if loaded is not None and Path(loaded.__file__).absolute() != PROOF_ROOT / (name + '.py'):
            raise ValueError('lcer.dependency_identity_mismatch')
    sys.path[:] = [str(PROOF_ROOT), *_STDLIB_PATHS]


_prepare_source_imports()

from live_cross_domain_evidence_round_trip import (
    FrozenObligationPlanCompiler,
    FrozenWireValidator,
    inspect_project_sources,
    parse_stored_json,
    select_frozen_case,
    source_file_bytes,
    stored_json_bytes,
    validate_python_import_paths,
)


class AcquisitionWorkspace:
    """Reserve fresh storage and derive only the frozen launch arguments.

    This owns directory and input preparation. It grants no source-dataflow,
    build, process, physical-world or release acceptance.
    """

    def __init__(self, contract_raw, repository_root, runtime_parent, output_root):
        self._contract_raw = contract_raw
        self._plan = FrozenObligationPlanCompiler(contract_raw).compile()
        self._repository_root = Path(repository_root).absolute()
        self._execution_root = PROOF_ROOT.parent
        if self._repository_root != Path('/Users/boandersson/Projects/CITY'):
            raise ValueError('lcer.acquisition_repository_invalid')
        self._source_snapshot = inspect_project_sources(contract_raw, self._repository_root)
        self._runtime_parent = self._destination(runtime_parent)
        self._output_root = self._destination(output_root)
        policy = self._plan['constitutional_policy']
        if (self._runtime_parent.is_relative_to(self._repository_root)
                or self._runtime_parent.is_relative_to(self._output_root)
                or self._output_root.is_relative_to(self._runtime_parent)
                or (self._output_root.is_relative_to(self._repository_root)
                    and self._output_root != self._repository_root / policy['runtime']['output_root'])):
            raise ValueError('lcer.acquisition_path_invalid')
        self._reserved = False
        self._identities = {}
        self._cases = set()
        self._launches = set()
        self._launch_ids = set()
        self._build_started = False
        self._build_capture = None

    @staticmethod
    def _destination(supplied):
        path = Path(supplied)
        if (not path.is_absolute() or '..' in path.parts or path != path.resolve()
                or any(item.is_symlink() for item in [path, *path.parents])
                or path.exists() or not path.parent.is_dir()):
            raise ValueError('lcer.acquisition_path_invalid')
        return path

    @staticmethod
    def _directory_identity(path):
        value = path.lstat()
        if (not stat.S_ISDIR(value.st_mode) or value.st_uid != os.getuid()
                or stat.S_IMODE(value.st_mode) != 0o700 or path != path.resolve()
                or any(item.is_symlink() for item in [path, *path.parents])):
            raise ValueError('lcer.acquisition_directory_changed')
        return value.st_dev, value.st_ino, value.st_uid

    def _mkdir(self, path):
        path.mkdir(mode=0o700)
        self._identities[path] = self._directory_identity(path)

    def verify(self):
        FrozenObligationPlanCompiler(self._contract_raw).validate(self._plan)
        if inspect_project_sources(self._contract_raw, self._repository_root) != self._source_snapshot:
            raise ValueError('lcer.acquisition_source_changed')
        if self._execution_root != self._repository_root:
            policy = self._plan['constitutional_policy']
            prefix = policy['runtime']['output_root'] + '/'
            # Both normal and direct calls authenticate a copied entrypoint's
            # complete declared source set against the actual CITY candidate.
            # Old canonical record paths remain physical CITY dependencies.
            for name in policy['release_members']:
                if not name.startswith(prefix):
                    copied = source_file_bytes(self._execution_root, name)
                    if copied != source_file_bytes(self._repository_root, name):
                        raise ValueError('lcer.dependency_identity_mismatch')
        for path, identity in self._identities.items():
            if self._directory_identity(path) != identity:
                raise ValueError('lcer.acquisition_directory_changed')

    def reserve(self):
        if self._reserved:
            raise ValueError('lcer.operation_sequence_invalid')
        self.verify()
        self._destination(self._runtime_parent)
        self._destination(self._output_root)
        # A partial reservation remains owned and cannot be retried or reused.
        self._reserved = True
        self._mkdir(self._runtime_parent)
        self._mkdir(self._output_root)

    def begin_case(self, case_id):
        if not self._reserved or case_id in self._cases:
            raise ValueError('lcer.operation_sequence_invalid')
        select_frozen_case(self._contract_raw, case_id)
        self.verify()
        self._cases.add(case_id)
        self._mkdir(self._runtime_parent / case_id)
        self._mkdir(self._output_root / case_id)

    def _require_build_source_audit(self):
        """Keep the direct compiler route closed while the audit is incomplete.

        There is deliberately no supplied report, boolean or fixture switch.
        Replace this denial only with the independently executed full audit
        and its fourteen owned adversaries, bound to this workspace's bytes.
        """
        raise ValueError('lcer.acquisition_implementation_incomplete')

    def build_candidate(self):
        """Guard the frozen compiler invocation before any build-side effect.

        Offline tests intercept both the incomplete audit boundary and the
        compiler call. Those fixtures confer no audit or build authority.
        """
        if not self._reserved or self._build_started:
            raise ValueError('lcer.operation_sequence_invalid')
        self.verify()
        self._require_build_source_audit()
        health = core_health(self._contract_raw, self._repository_root)
        python_runtime = current_python_runtime()
        policy = self._plan['constitutional_policy']
        argv = [value.format(absolute_city_project=str(self._repository_root / policy['runtime']['project']))
                for value in policy['build_argv']]
        log_path = self._output_root / 'build.log'
        # The latch precedes the external call. Failure, interruption and an
        # intercepted test boundary all consume this workspace's invocation.
        self._build_started = True
        started = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        with log_path.open('xb') as log:
            log.write(b'CITY_LCER_PYTHON ' + stored_json_bytes(python_runtime))
            log.flush()
            result = subprocess.run(argv, cwd=str(self._repository_root),
                                    stdout=log, stderr=subprocess.STDOUT, timeout=900)
            log.flush()
            os.fsync(log.fileno())
        finished = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        self.verify()
        if current_python_runtime() != python_runtime:
            raise ValueError('lcer.python_runtime_changed')
        log_identity = external_file_identity(log_path)
        self._build_capture = {'argv': argv, 'cwd': str(self._repository_root),
                               'started_at': started, 'finished_at': finished,
                               'returncode': result.returncode,
                               'log': {'path': 'build.log', 'sha256': log_identity['sha256'],
                                       'size_bytes': log_identity['size_bytes']},
                               'source_files': self._source_snapshot,
                               'core_dependencies': health['files'],
                               'python_runtime': python_runtime}
        if result.returncode != 0:
            raise ValueError('lcer.build_failed')
        return parse_stored_json(stored_json_bytes(self._build_capture))

    def prepare_launch(self, case_id, domain, replacement=False):
        if (case_id not in self._cases or domain not in ('domain_A', 'domain_B')
                or type(replacement) is not bool or (replacement and (case_id != 'F07' or domain != 'domain_A'))):
            raise ValueError('lcer.operation_sequence_invalid')
        key = (case_id, domain, replacement)
        if key in self._launches or (replacement and (case_id, domain, False) not in self._launches):
            raise ValueError('lcer.operation_sequence_invalid')
        self.verify()
        self._launches.add(key)
        label = 'replacement' if replacement else domain
        directory = self._runtime_parent / case_id / label
        self._mkdir(directory)
        for name in ('home', 'user', 'tmp'):
            self._mkdir(directory / name)
        launch_id = os.urandom(16).hex()
        if launch_id in self._launch_ids:
            raise ValueError('lcer.launch_identity_repeated')
        self._launch_ids.add(launch_id)
        policy = self._plan['constitutional_policy']
        arguments = {'engine': policy['runtime']['engine'],
                     'absolute_city_project': str(self._repository_root / policy['runtime']['project']),
                     'domain': domain, 'witness_id': case_id, 'launch_id': launch_id,
                     'absolute_domain_root': str(directory),
                     'observed_operator_user': pwd.getpwuid(os.getuid()).pw_name}
        argv = [value.format_map(arguments) for value in policy['launch_argv']]
        environment = {key: value.format_map(arguments) for key, value in policy['launch_environment'].items()}
        FrozenWireValidator(self._contract_raw).validate('environment', environment)
        return {'witness_id': case_id, 'domain': domain, 'launch_id': launch_id,
                'cwd': str(self._repository_root), 'argv': argv, 'environment': environment,
                'process_root_realpath': str(directory)}


class AcquisitionPackageWriter:
    """Write the frozen byte graph after its actual producers have run.

    This checks serialization, identities and graph closure. It does not replace
    the pre-build source audit, native input derivation or independent live
    verification. A complete byte graph alone is not an accepted release.
    """

    def __init__(self, workspace, budget):
        if not isinstance(workspace, AcquisitionWorkspace) or not workspace._reserved or not isinstance(budget, CaptureBudget):
            raise ValueError('lcer.operation_sequence_invalid')
        self.workspace, self.budget = workspace, budget
        self._raw = workspace._contract_raw
        self.policy = FrozenObligationPlanCompiler(self._raw).compile()['constitutional_policy']
        self.validator = FrozenWireValidator(self._raw)
        self._identity = self._git_identity()
        self._written = {}
        self._references_attempted = False
        self._build_attempted = False
        self._finalize_attempted = False
        self._manifest = workspace._execution_root / self.policy['release_manifest']
        if self._manifest.exists() or self._manifest.is_symlink():
            raise ValueError('lcer.release_manifest_exists')
        self.verify()

    def _git_identity(self):
        raw = subprocess.check_output(['/usr/bin/git', 'rev-parse', '--show-toplevel', 'HEAD', 'HEAD^{tree}'],
                                      cwd=self.workspace._repository_root,
                                      env={'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C'}, timeout=30)
        lines = raw.decode('utf-8').splitlines()
        if (len(lines) != 3 or lines[0] != str(self.workspace._repository_root)
                or any(re.fullmatch('[0-9a-f]{40}', value) is None for value in lines[1:])):
            raise ValueError('lcer.source_git_identity_invalid')
        return {'source_commit': lines[1], 'source_tree': lines[2]}

    @property
    def source_identity(self):
        return dict(self._identity)

    def _artifact(self, name):
        if name not in self.policy['artifact_relative_paths']:
            raise ValueError('lcer.artifact_path_invalid')
        path = self.workspace._output_root / name
        if path.is_symlink() or path.resolve() != path or not path.is_file():
            raise ValueError('lcer.artifact_path_invalid')
        identity = external_file_identity(path)
        return {'path': name, 'sha256': identity['sha256'], 'size_bytes': identity['size_bytes']}

    def verify(self):
        self.workspace.verify()
        frozen = FrozenObligationPlanCompiler(self._raw).compile()['constitutional_policy']
        if self.policy != frozen or self._git_identity() != self._identity:
            raise ValueError('lcer.acquisition_source_changed')
        for name, record in self._written.items():
            if self._artifact(name) != record:
                raise ValueError('lcer.artifact_changed_after_write')

    def _write(self, name, raw):
        if name not in self.policy['artifact_relative_paths'] or name in self._written:
            raise ValueError('lcer.artifact_path_invalid')
        path = self.workspace._output_root / name
        if path.resolve() != path or path.is_symlink() or not path.parent.is_dir():
            raise ValueError('lcer.artifact_path_invalid')
        self.budget.claim(len(raw))
        with path.open('xb') as stream:
            if stream.write(raw) != len(raw):
                raise OSError('lcer.artifact_write_failed')
            stream.flush()
            os.fsync(stream.fileno())
        record = self._artifact(name)
        if record['sha256'] != hashlib.sha256(raw).hexdigest() or record['size_bytes'] != len(raw):
            raise ValueError('lcer.artifact_write_invalid')
        self._written[name] = record
        return dict(record)

    def write_references(self):
        if self._references_attempted or self._build_attempted or self._finalize_attempted:
            raise ValueError('lcer.operation_sequence_invalid')
        self.verify()
        self._references_attempted = True
        self.workspace._mkdir(self.workspace._output_root / 'canonical')
        result = []
        for symbol in ('R0', 'R1', 'QA', 'QB'):
            source = 'proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_' + symbol + '.json'
            raw = source_file_bytes(self.workspace._repository_root, source, self.policy['canonical_records'][source])
            result.append(self._write('canonical/' + symbol + '.json', raw))
        self.verify()
        return result

    def write_build(self, record):
        if not self._references_attempted or self._build_attempted or self._finalize_attempted:
            raise ValueError('lcer.operation_sequence_invalid')
        self.verify()
        self._build_attempted = True
        self.validator.validate('build_record', record)
        captured = self.workspace._build_capture
        if captured is None:
            raise ValueError('lcer.build_capture_missing')
        if (record['returncode'] != 0 or captured['returncode'] != 0
                or any(record[key] != captured[key] for key in ('argv', 'cwd', 'returncode', 'started_at', 'finished_at', 'log'))
                or any(record[key] != value for key, value in self._identity.items())
                or record['log'] != self._artifact('build.log')
                or record['editor']['realpath'] != self.policy['runtime']['engine']
                or record['project'] != external_file_identity(self.workspace._repository_root / self.policy['runtime']['project'])
                or record['source_audit']['returncode'] != 0):
            raise ValueError('lcer.build_record_invalid')
        # The enclosing producer must supply the independently audited source
        # report and observed native inventories. Shape/argv equality here is
        # only packaging validation; it cannot establish those semantics.
        result = self._write('build.json', stored_json_bytes(record))
        self.verify()
        return result

    def observed_build_record(self, runtime_inputs, source_audit, launches):
        """Assemble the frozen record from one captured, observed acquisition.

        This binds producer records and actual file bytes. It does not turn
        the supplied audit report into an independent semantic verdict. The
        pre-build audit gate and final independent verifier remain mandatory.
        No compiler, child process or artifact write occurs in this method.
        """
        self.verify()
        if (not isinstance(runtime_inputs, RuntimeBuildInputInventory)
                or runtime_inputs._build._workspace is not self.workspace):
            raise ValueError('lcer.runtime_build_capture_missing')
        captured = self.workspace._build_capture
        if captured is None or captured['returncode'] != 0:
            raise ValueError('lcer.build_capture_missing')
        capture_raw = stored_json_bytes(captured)
        if runtime_inputs._build._capture_raw != capture_raw:
            raise ValueError('lcer.build_capture_changed')
        captured = parse_stored_json(capture_raw)
        runtime_inputs.verify()
        native = runtime_inputs._build.snapshot()
        project = self.workspace._repository_root / self.policy['runtime']['project']
        if (native['editor']['realpath'] != self.policy['runtime']['engine']
                or native['project'] != external_file_identity(project)
                or captured['source_files'] != self.workspace._source_snapshot
                or captured['log'] != self._artifact('build.log')):
            raise ValueError('lcer.build_record_invalid')

        # Cover every original process plus the one frozen replacement. A
        # valid subset of observations cannot stand in for the acquisition.
        cases = set(self.policy['artifact_hash_graph']['case_ids'])
        expected = {(case, domain, False) for case in cases for domain in ('domain_A', 'domain_B')}
        expected.add(('F07', 'domain_A', True))
        if (type(launches) is not list or len(launches) != len(expected)
                or any(type(row) is not dict or set(row) != {'witness_id', 'domain', 'launch_id'}
                       or any(type(value) is not str or not value for value in row.values()) for row in launches)
                or self.workspace._cases != cases or self.workspace._launches != expected):
            raise ValueError('lcer.runtime_input_launches_incomplete')
        launch_ids = [row['launch_id'] for row in launches]
        pairs = sorted((row['witness_id'], row['domain']) for row in launches)
        if (len(set(launch_ids)) != len(expected) or set(launch_ids) != self.workspace._launch_ids
                or pairs != sorted((case, domain) for case, domain, _ in expected)):
            raise ValueError('lcer.runtime_input_launches_incomplete')
        runtime_inputs.require_launches(launches)

        audit = parse_stored_json(stored_json_bytes(source_audit))
        self.validator.validate('source_audit', audit)
        required_files = set(self.policy['planned_source_paths']) | {
            name for group in ('predecessors', 'unchanged_dependencies') for name in self.policy[group]
            if name.endswith('.py')}
        audited_names = [row['path'] for row in audit['files']]
        prefix = self.policy['runtime']['output_root'] + '/'
        source_members = {name for name in self.policy['release_members'] if not name.startswith(prefix)}
        mutations = audit['rejected_mutations']
        required_mutations = self.policy['process_input_contract']['source_negative_cases']
        if (audit['returncode'] != 0 or not audit['argv'] or not audit['edges']
                or len(audited_names) != len(set(audited_names))
                or not required_files <= set(audited_names) <= source_members
                or any(edge['path'] not in audited_names for edge in audit['edges'])
                or len(mutations) != len(required_mutations) or set(mutations) != set(required_mutations)):
            raise ValueError('lcer.source_audit_record_invalid')
        for row in audit['files']:
            raw = source_file_bytes(self.workspace._repository_root, row['path'])
            if row['sha256'] != hashlib.sha256(raw).hexdigest() or row['size_bytes'] != len(raw):
                raise ValueError('lcer.source_audit_record_changed')
        record = {'schema': 'city.live_evidence_build.v1', **self._identity,
                  **{key: captured[key] for key in ('argv', 'cwd', 'returncode', 'started_at', 'finished_at', 'log')},
                  **{key: native[key] for key in ('editor', 'project', 'modules')},
                  'external_inputs': runtime_inputs.external_inputs(), 'source_audit': audit}
        self.validator.validate('build_record', record)
        runtime_inputs.verify()
        self.verify()
        if stored_json_bytes(self.workspace._build_capture) != capture_raw:
            raise ValueError('lcer.build_capture_changed')
        return parse_stored_json(stored_json_bytes(record))

    def _check_case(self, name, raw, hashes):
        case = self.validator.parse('case_record', raw)
        plan = select_frozen_case(self._raw, name)
        targets = self.policy['artifact_hash_graph']['case_record_targets'][name]
        rows = case['artifact_sha256']
        if (case['witness_id'] != name or len(rows) != len(targets) or {row['path'] for row in rows} != set(targets)
                or any(row != hashes[row['path']] for row in rows)):
            raise ValueError('lcer.case_artifact_graph_invalid')
        references = {symbol: (self.workspace._output_root / 'canonical' / (symbol + '.json')).read_bytes().decode('utf-8')
                      for symbol in ('R0', 'R1')}
        canonical = case['canonical_artifacts']
        if (canonical['initial_raw_utf8'] != references['R0'] or canonical['published_raw_utf8'] not in (None, references['R1'])
                or canonical['terminal_raw_utf8'] != (canonical['published_raw_utf8'] or references['R0'])
                or case['claims']['canonical_commit'] != (canonical['published_raw_utf8'] is not None)):
            raise ValueError('lcer.case_canonical_record_invalid')
        if case['status'] == 'acquisition_failure':
            if not case['failure_codes'] or case['claims']['synchronized_representation']:
                raise ValueError('lcer.case_status_invalid')
            return False
        expected = 'accepted' if plan['kind'] == 'witness' else 'expected_failure'
        failures = ([] if plan['kind'] == 'witness' else
                    [plan['failure_family']['failure_code']] if plan['kind'] == 'failure' else [plan['underlying_code']])
        if (case['status'] != expected or case['failure_codes'] != failures
                or case['claims']['synchronized_representation'] != (plan['kind'] == 'witness')
                or case['claims']['canonical_commit'] != bool(plan['publication_count'])
                or canonical['terminal_raw_utf8'] != references[plan['terminal_canonical']]):
            raise ValueError('lcer.case_status_invalid')
        return True

    def finalize(self):
        if self._finalize_attempted or 'build.json' not in self._written:
            raise ValueError('lcer.operation_sequence_invalid')
        self._finalize_attempted = True
        self.verify()
        graph = self.policy['artifact_hash_graph']
        found = []
        for path in self.workspace._output_root.rglob('*'):
            if path.is_symlink():
                raise ValueError('lcer.artifact_path_invalid')
            if path.is_file():
                found.append(path.relative_to(self.workspace._output_root).as_posix())
        if len(found) != len(graph['acquisition_targets']) or set(found) != set(graph['acquisition_targets']):
            raise ValueError('lcer.acquisition_artifact_membership_invalid')
        hashes = {name: self._artifact(name) for name in graph['acquisition_targets']}
        cases = []
        complete = True
        for name in graph['case_ids']:
            relative = name + '/record.json'
            raw = (self.workspace._output_root / relative).read_bytes()
            if hashlib.sha256(raw).hexdigest() != hashes[relative]['sha256']:
                raise ValueError('lcer.case_artifact_changed')
            complete = self._check_case(name, raw, hashes) and complete
            cases.append({'witness_id': name, 'record_path': relative, 'record_sha256': hashes[relative]['sha256']})
        acquisition = {'schema': 'city.live_evidence_acquisition.v1', **self._identity,
                       'build_sha256': hashes['build.json']['sha256'], 'cases': cases,
                       'artifact_members': self.policy['artifact_relative_paths'],
                       'artifact_hashes': [hashes[name] for name in graph['acquisition_targets']],
                       'status': 'complete' if complete else 'failed',
                       'claims': {'synchronized_representation': complete, 'canonical_commit': complete,
                                  'production_ready': False, 'trusted_ci': False, 'game_sealed': False}}
        self.validator.validate('acquisition_record', acquisition)
        hashes['acquisition.json'] = self._write('acquisition.json', stored_json_bytes(acquisition))
        self.verify()
        prefix = self.policy['runtime']['output_root'] + '/'
        lines = []
        for name in sorted(self.policy['release_members']):
            if name.startswith(prefix):
                value = hashes[name[len(prefix):]]['sha256']
            else:
                value = hashlib.sha256(source_file_bytes(self.workspace._execution_root, name)).hexdigest()
            lines.append(value + '  ' + name + '\n')
        raw = ''.join(lines).encode('ascii')
        self.budget.claim(len(raw))
        if self._manifest.is_symlink() or self._manifest.resolve() != self._manifest:
            raise ValueError('lcer.release_manifest_path_invalid')
        with self._manifest.open('xb') as stream:
            if stream.write(raw) != len(raw):
                raise OSError('lcer.release_manifest_write_failed')
            stream.flush()
            os.fsync(stream.fileno())
        self.verify()
        if self._manifest.read_bytes() != raw:
            raise ValueError('lcer.release_manifest_write_invalid')
        for name, row in hashes.items():
            if self._artifact(name) != row:
                raise ValueError('lcer.artifact_changed_after_write')
        return {'acquisition': dict(hashes['acquisition.json']), 'manifest_path': str(self._manifest),
                'manifest_sha256': hashlib.sha256(raw).hexdigest(), 'artifact_count': len(hashes),
                'release_member_count': len(lines), 'byte_graph_complete': True, 'live_acceptance_verified': False}


class _BsdProcess(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in (
        "flags", "status", "xstatus", "pid", "ppid", "uid", "gid", "ruid", "rgid", "svuid", "svgid", "reserved"
    )] + [("comm", ctypes.c_char * 16), ("name", ctypes.c_char * 32)] + [
        (name, ctypes.c_uint32) for name in ("nfiles", "pgid", "pjobc", "tdev", "tpgid")
    ] + [("nice", ctypes.c_int32), ("seconds", ctypes.c_uint64), ("microseconds", ctypes.c_uint64)]


class _VnodeStat(ctypes.Structure):
    _fields_ = [("dev", ctypes.c_uint32), ("mode", ctypes.c_uint16), ("nlink", ctypes.c_uint16),
                ("ino", ctypes.c_uint64), ("uid", ctypes.c_uint32), ("gid", ctypes.c_uint32)] + [
        (name, ctypes.c_int64) for name in (
            "atime", "atimensec", "mtime", "mtimensec", "ctime", "ctimensec", "birthtime", "birthtimensec", "size", "blocks"
        )
    ] + [("blksize", ctypes.c_int32), ("flags", ctypes.c_uint32), ("gen", ctypes.c_uint32),
         ("rdev", ctypes.c_uint32), ("spare", ctypes.c_int64 * 2)]


class _VnodeInfo(ctypes.Structure):
    _fields_ = [("stat", _VnodeStat), ("type", ctypes.c_int32), ("pad", ctypes.c_int32),
                ("fsid", ctypes.c_int32 * 2)]


class _VnodePath(ctypes.Structure):
    _fields_ = [("info", _VnodeInfo), ("path", ctypes.c_char * 1024)]


class _ProcessPaths(ctypes.Structure):
    _fields_ = [("cwd", _VnodePath), ("root", _VnodePath)]


class _FileInfo(ctypes.Structure):
    _fields_ = [("flags", ctypes.c_uint32), ("status", ctypes.c_uint32), ("offset", ctypes.c_int64),
                ("type", ctypes.c_int32), ("guardflags", ctypes.c_uint32)]


class _PipeInfo(ctypes.Structure):
    _fields_ = [("file", _FileInfo), ("stat", _VnodeStat), ("handle", ctypes.c_uint64),
                ("peer", ctypes.c_uint64), ("status", ctypes.c_int32), ("reserved", ctypes.c_int32)]


class _DescriptorInfo(ctypes.Structure):
    _fields_ = [("fd", ctypes.c_int32), ("kind", ctypes.c_uint32)]


class _VnodeDescriptor(ctypes.Structure):
    _fields_ = [("file", _FileInfo), ("vnode", _VnodePath)]


def external_file_identity(path):
    """Hash a real external file and reject mutation during the read."""
    actual = Path(path).resolve(strict=True)
    with actual.open("rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("lcer.external_input_invalid")
        value = hashlib.sha256()
        count = 0
        while True:
            raw = stream.read(1024 * 1024)
            if not raw:
                break
            value.update(raw)
            count += len(raw)
        after = os.fstat(stream.fileno())
    current = actual.stat()
    before_key = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    if (count != before.st_size or before_key != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            or before_key != (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns, current.st_ctime_ns)):
        raise ValueError("lcer.external_input_changed")
    return {"realpath": str(actual), "sha256": value.hexdigest(), "size_bytes": count}


def current_python_runtime():
    """Observe this interpreter; a supplied executable path is never run."""
    observer = MacProcessObserver()
    process = observer.identity(os.getpid())
    birth = process['macos_birth_tuple']
    paths = observer.paths(process['pid'], birth)
    executable = external_file_identity(paths['executable_realpath'])
    runtime = {'schema': 'city.live_evidence_python_runtime.v1', 'executable': executable,
               'implementation': sys.implementation.name, 'version': sys.version,
               'version_info': list(sys.version_info)}
    if (observer.identity(os.getpid()) != process or observer.paths(process['pid'], birth) != paths
            or external_file_identity(paths['executable_realpath']) != executable
            or sys.implementation.name != runtime['implementation'] or sys.version != runtime['version']
            or list(sys.version_info) != runtime['version_info']):
        raise ValueError('lcer.python_runtime_changed')
    return runtime


def python_runtime_from_build_log(contract_raw, raw):
    """Read the parent's single runtime prelude; leave compiler bytes intact."""
    line, separator, remaining = raw.partition(b'\n')
    prefix = b'CITY_LCER_PYTHON '
    if (not separator or not line.startswith(prefix)
            or any(row.startswith(prefix) for row in remaining.splitlines())):
        raise ValueError('lcer.python_runtime_log_invalid')
    record = parse_stored_json(line[len(prefix):] + b'\n')
    if (type(record) is not dict or set(record) != {'schema', 'executable', 'implementation', 'version', 'version_info'}
            or record['schema'] != 'city.live_evidence_python_runtime.v1'
            or any(type(record[key]) is not str or not record[key] for key in ('implementation', 'version'))
            or type(record['version_info']) is not list or len(record['version_info']) != 5
            or any(type(record['version_info'][index]) is not int or record['version_info'][index] < 0 for index in (0, 1, 2, 4))
            or record['version_info'][3] not in ('alpha', 'beta', 'candidate', 'final')
            or stored_json_bytes(record) != line[len(prefix):] + b'\n'):
        raise ValueError('lcer.python_runtime_log_invalid')
    FrozenWireValidator(contract_raw).validate('file_identity', record['executable'])
    return record, remaining


def macho_file_images(path):
    """Read architecture/LC_UUID from each actual thin or universal slice."""
    file = external_file_identity(path)
    result = []
    with Path(file['realpath']).open('rb') as stream:
        magic = stream.read(4)
        slices = []
        if magic in (b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf'):
            raw_count = stream.read(4)
            if len(raw_count) != 4:
                raise ValueError('lcer.image_identity_invalid')
            count = struct.unpack('>I', raw_count)[0]
            if not 1 <= count <= 32:
                raise ValueError('lcer.image_identity_invalid')
            wide = magic == b'\xca\xfe\xba\xbf'
            width = 32 if wide else 20
            for _ in range(count):
                raw = stream.read(width)
                if len(raw) != width:
                    raise ValueError('lcer.image_identity_invalid')
                row = struct.unpack('>iiQQII' if wide else '>iiIII', raw)
                cpu, subtype, offset, size, alignment = row[:5]
                if (alignment > 31 or offset % (1 << alignment) or offset < 8 + count * width or
                        size < 32 or offset + size > file['size_bytes']):
                    raise ValueError('lcer.image_identity_invalid')
                slices.append((offset, size, cpu, subtype))
            ordered = sorted(slices)
            if any(left[0] + left[1] > right[0] for left, right in zip(ordered, ordered[1:])):
                raise ValueError('lcer.image_identity_invalid')
        elif magic == b'\xcf\xfa\xed\xfe':
            slices = [(0, file['size_bytes'], None, None)]
        else:
            raise ValueError('lcer.image_identity_invalid')
        for offset, size, expected_cpu, expected_subtype in slices:
            stream.seek(offset)
            header = stream.read(32)
            if len(header) != 32:
                raise ValueError('lcer.image_identity_invalid')
            magic, cpu, subtype, _, count, command_size, _, _ = struct.unpack('<IiiIIIII', header)
            if (magic != 0xfeedfacf or (expected_cpu is not None and (cpu, subtype) != (expected_cpu, expected_subtype))
                    or not 1 <= count <= command_size // 8 or command_size > size - 32):
                raise ValueError('lcer.image_identity_invalid')
            if cpu == 0x0100000c:
                architecture = 'arm64e' if subtype & 0x00ffffff == 2 else 'arm64'
            elif cpu == 0x01000007:
                architecture = 'x86_64'
            else:
                raise ValueError('lcer.image_identity_invalid')
            commands = stream.read(command_size)
            index = 0
            uuid = None
            for _ in range(count):
                if index + 8 > len(commands):
                    raise ValueError('lcer.image_identity_invalid')
                kind, length = struct.unpack_from('<II', commands, index)
                if length < 8 or length % 8 or index + length > len(commands):
                    raise ValueError('lcer.image_identity_invalid')
                if kind == 0x1b:
                    if length != 24 or uuid is not None:
                        raise ValueError('lcer.image_identity_invalid')
                    raw_uuid = commands[index + 8:index + 24].hex()
                    uuid = '-'.join(raw_uuid[a:b] for a, b in [(0, 8), (8, 12), (12, 16), (16, 20), (20, 32)])
                index += length
            if index != command_size or uuid is None:
                raise ValueError('lcer.image_identity_invalid')
            result.append({'realpath': file['realpath'], 'sha256': file['sha256'], 'macho_uuid': uuid,
                           'architecture': architecture, 'source': 'dyld'})
    if len({row['architecture'] for row in result}) != len(result) or file != external_file_identity(path):
        raise ValueError('lcer.image_identity_invalid')
    return sorted(result, key=lambda row: row['architecture'])


def dyld_process_prefix(raw, address):
    """Read the LP64 dyld_all_image_infos prefix declared by the Mac SDK.

    The source is a bounded kernel copy, never a supplied pointer dereference.
    Version 15 retains this prefix in later SDKs. The self pointer closes the
    join to TASK_DYLD_INFO rather than accepting a plausible UUID byte string.
    """
    if (type(raw) is not bytes or len(raw) != 200 or type(address) is not int
            or address <= 0 or address % 16):
        raise ValueError('lcer.dyld_process_observation_invalid')
    version, count = struct.unpack_from('<II', raw)
    self_address = struct.unpack_from('<Q', raw, 104)[0]
    uuid = raw[160:176]
    base, timestamp = struct.unpack_from('<QQ', raw, 176)
    if (version < 15 or raw[24] != 0 or raw[25] != 1 or self_address != address
            or not any(uuid) or not base or not timestamp or not count):
        raise ValueError('lcer.dyld_process_observation_invalid')
    return {'version': version, 'image_count': count, 'all_image_info_address': address,
            'shared_cache_uuid': uuid.hex(), 'shared_cache_base_address': base,
            'info_array_change_timestamp': timestamp,
            'prefix_sha256': hashlib.sha256(raw).hexdigest()}


def current_dyld_process():
    """Read this process's loader through task_info and checked kernel copies."""
    if sys.platform != 'darwin' or ctypes.sizeof(ctypes.c_void_p) != 8:
        raise ValueError('lcer.dyld_process_observation_invalid')
    library = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
    port = ctypes.c_uint32.in_dll(library, 'mach_task_self_').value
    task_info = library.task_info
    task_info.restype = ctypes.c_int
    task_info.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32),
                          ctypes.POINTER(ctypes.c_uint32)]
    # task_info.h packs task_dyld_info to four-byte alignment: Q, Q, i.
    task = (ctypes.c_uint32 * 5)()
    count = ctypes.c_uint32(5)
    if task_info(port, 17, task, ctypes.byref(count)) != 0 or count.value != 5:
        raise ValueError('lcer.dyld_process_observation_invalid')
    address, size, image_format = struct.unpack('<QQi', bytes(task))
    if image_format != 1 or size < 200 or address == 0 or address % 16:
        raise ValueError('lcer.dyld_process_observation_invalid')
    read = library.mach_vm_read_overwrite
    read.restype = ctypes.c_int
    read.argtypes = [ctypes.c_uint32, ctypes.c_uint64, ctypes.c_uint64,
                    ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)]
    buffer = ctypes.create_string_buffer(200)
    copied = ctypes.c_uint64()
    if read(port, address, 200, ctypes.addressof(buffer), ctypes.byref(copied)) != 0 or copied.value != 200:
        raise ValueError('lcer.dyld_process_observation_invalid')
    first = dyld_process_prefix(buffer.raw, address)
    task_after = (ctypes.c_uint32 * 5)()
    count_after = ctypes.c_uint32(5)
    if (task_info(port, 17, task_after, ctypes.byref(count_after)) != 0 or count_after.value != 5
            or bytes(task_after) != bytes(task)
            or read(port, address, 200, ctypes.addressof(buffer), ctypes.byref(copied)) != 0 or copied.value != 200
            or dyld_process_prefix(buffer.raw, address) != first):
        raise ValueError('lcer.dyld_process_observation_changed')
    return {**first, 'all_image_info_size': size, 'all_image_info_format': image_format}


def select_dyld_cache(shared_cache_uuid, candidates):
    """Select one real cache by observed UUID; aliases are not extra caches."""
    if (type(shared_cache_uuid) is not str or re.fullmatch('[0-9a-f]{32}', shared_cache_uuid) is None
            or shared_cache_uuid == '0' * 32 or type(candidates) not in (list, tuple)):
        raise ValueError('lcer.dyld_cache_selection_invalid')
    matches = {}
    for supplied in candidates:
        path = Path(supplied)
        if not path.is_absolute():
            raise ValueError('lcer.dyld_cache_selection_invalid')
        try:
            actual = path.resolve(strict=True)
        except FileNotFoundError:
            continue
        with actual.open('rb') as stream:
            header = stream.read(104)
        if len(header) == 104 and header[:7] == b'dyld_v1' and header[88:104].hex() == shared_cache_uuid:
            if str(actual) in matches and matches[str(actual)] != header:
                raise ValueError('lcer.external_input_changed')
            matches[str(actual)] = header
    if len(matches) != 1:
        raise ValueError('lcer.dyld_cache_selection_invalid')
    path, header = next(iter(matches.items()))
    identity = external_file_identity(path)
    with Path(path).open('rb') as stream:
        if stream.read(104) != header:
            raise ValueError('lcer.external_input_changed')
    return identity


def current_dyld_cache():
    """Bind the current loader's UUID to the complete on-disk cache inventory."""
    before = current_dyld_process()
    directories = ('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld', '/System/Library/dyld')
    names = ('dyld_shared_cache_arm64e', 'dyld_shared_cache_x86_64')
    selected = select_dyld_cache(before['shared_cache_uuid'],
                                 [str(Path(directory) / name) for directory in directories for name in names])
    inventory = dyld_cache_inventory(selected['realpath'])
    if (inventory['main'] != selected or not inventory['cache_uuids']
            or inventory['cache_uuids'][0].replace('-', '') != before['shared_cache_uuid']
            or current_dyld_process() != before):
        raise ValueError('lcer.dyld_cache_observation_changed')
    return {'process': before, 'inventory': inventory}


def dyld_cache_inventory(path):
    """Bind modern macOS cache files, mappings and embedded Mach-O identities.

    Layout: Apple's mach-o/dyld_cache_format.h. Cache metadata selects bounded
    byte ranges only; it never selects canonical or representation behavior.
    """
    main = external_file_identity(path)
    files, mappings, text_rows, cache_uuids = [], [], [], []

    def read_at(stream, offset, count, size):
        if offset < 0 or count < 0 or offset + count > size:
            raise ValueError('lcer.dyld_cache_invalid')
        stream.seek(offset)
        value = stream.read(count)
        if len(value) != count:
            raise ValueError('lcer.dyld_cache_invalid')
        return value

    def uuid_text(raw):
        if len(raw) != 16 or raw == bytes(16):
            raise ValueError('lcer.dyld_cache_invalid')
        value = raw.hex()
        return '-'.join((value[:8], value[8:12], value[12:16], value[16:20], value[20:]))

    pending = [(main, None, None)]
    expected_architecture = None
    main_base = None
    primary_text_index = None
    for file, expected_uuid, expected_offset in pending:
        with Path(file['realpath']).open('rb') as stream:
            size = file['size_bytes']
            header = read_at(stream, 0, 464, size)
            magic = header[:16].rstrip(b'\0')
            architecture = {b'dyld_v1  arm64e': 'arm64e', b'dyld_v1   arm64': 'arm64',
                            b'dyld_v1  x86_64': 'x86_64', b'dyld_v1 x86_64h': 'x86_64'}.get(magic)
            if architecture is None:
                raise ValueError('lcer.dyld_cache_invalid')
            if expected_architecture is None:
                expected_architecture = architecture
            if architecture != expected_architecture:
                raise ValueError('lcer.dyld_cache_invalid')
            mapping_offset, mapping_count = struct.unpack_from('<II', header, 16)
            # v2 subcache entries require the cacheSubType-era header. Earlier
            # layouts are rejected rather than guessed from filename suffixes.
            if mapping_offset < 464 or not 1 <= mapping_count <= 64:
                raise ValueError('lcer.dyld_cache_invalid')
            uuid = uuid_text(header[88:104])
            if uuid in cache_uuids or (expected_uuid is not None and uuid != expected_uuid):
                raise ValueError('lcer.dyld_cache_invalid')
            cache_uuids.append(uuid)
            local = []
            for index in range(mapping_count):
                raw = read_at(stream, mapping_offset + 32 * index, 32, size)
                address, length, offset, maximum, initial = struct.unpack('<QQQII', raw)
                if (not address or not length or offset + length > size or address + length >= 1 << 64 or
                        maximum & ~7 or initial & ~maximum):
                    raise ValueError('lcer.dyld_cache_invalid')
                local.append({'address': address, 'size': length, 'offset': offset,
                              'max_protection': maximum, 'initial_protection': initial, 'file': file['realpath']})
            if main_base is None:
                main_base = min(row['address'] for row in local)
            elif min(row['address'] for row in local) != main_base + expected_offset:
                raise ValueError('lcer.dyld_cache_invalid')
            mappings.extend(local)
            sub_offset, sub_count = struct.unpack_from('<II', header, 392)
            if sub_count > 64 or (expected_uuid is not None and sub_count):
                raise ValueError('lcer.dyld_cache_invalid')
            suffixes = set()
            for index in range(sub_count):
                raw = read_at(stream, sub_offset + 56 * index, 56, size)
                sub_uuid = uuid_text(raw[:16])
                vm_offset = struct.unpack_from('<Q', raw, 16)[0]
                suffix, separator, padding = raw[24:].partition(b'\0')
                if (not separator or any(padding) or
                        re.fullmatch(rb'\.[0-9]+(?:\.[A-Za-z0-9_]+)*', suffix) is None or suffix in suffixes):
                    raise ValueError('lcer.dyld_cache_invalid')
                suffixes.add(suffix)
                subpath = file['realpath'] + suffix.decode('ascii')
                pending.append((external_file_identity(subpath), sub_uuid, vm_offset))
            text_offset, text_count = struct.unpack_from('<QQ', header, 136)
            image_offset, image_count = struct.unpack_from('<II', header, 448)
            if text_count > 100000 or image_count != text_count or (expected_uuid is None and not text_count):
                raise ValueError('lcer.dyld_cache_invalid')

            def image_path(offset):
                raw = read_at(stream, offset, min(4096, size - offset), size)
                value, separator, _ = raw.partition(b'\0')
                if not separator:
                    raise ValueError('lcer.dyld_cache_invalid')
                value = value.decode('utf-8', 'strict')
                if not value.startswith('/') or str(Path(value)) != value or '..' in Path(value).parts:
                    raise ValueError('lcer.dyld_cache_invalid')
                return value

            text_index, image_index = {}, {}
            for index in range(text_count):
                raw = read_at(stream, text_offset + index * 32, 32, size)
                address, length, name_offset = struct.unpack_from('<QII', raw, 16)
                name = image_path(name_offset)
                if name in text_index or not length:
                    raise ValueError('lcer.dyld_cache_invalid')
                text_index[name] = {'realpath': name, 'macho_uuid': uuid_text(raw[:16]),
                                    'address': address, 'text_size': length}
                raw = read_at(stream, image_offset + index * 32, 32, size)
                address, _, _, name_offset, pad = struct.unpack('<QQQII', raw)
                name = image_path(name_offset)
                if name in image_index or pad:
                    raise ValueError('lcer.dyld_cache_invalid')
                image_index[name] = address
            if {name: row['address'] for name, row in text_index.items()} != image_index:
                raise ValueError('lcer.dyld_cache_invalid')
            if primary_text_index is None:
                primary_text_index = text_index
                text_rows.extend(text_index.values())
            elif text_index and text_index != primary_text_index:
                # Some current subcaches repeat the main image index. Those
                # are exact replicas, not additional or competing images.
                raise ValueError('lcer.dyld_cache_invalid')
            files.append(file)
    ordered = sorted(mappings, key=lambda row: row['address'])
    if any(a['address'] + a['size'] > b['address'] for a, b in zip(ordered, ordered[1:])):
        raise ValueError('lcer.dyld_cache_invalid')
    for file in files:
        local = sorted((row for row in mappings if row['file'] == file['realpath']), key=lambda row: row['offset'])
        if any(a['offset'] + a['size'] > b['offset'] for a, b in zip(local, local[1:])):
            raise ValueError('lcer.dyld_cache_invalid')
    images = []
    streams = {}
    try:
        for file in files:
            streams[file['realpath']] = Path(file['realpath']).open('rb')
        for row in text_rows:
            candidates = [m for m in mappings if m['address'] <= row['address'] and
                          row['address'] + row['text_size'] <= m['address'] + m['size'] and m['initial_protection'] & 4]
            if len(candidates) != 1:
                raise ValueError('lcer.dyld_cache_invalid')
            mapping = candidates[0]
            stream = streams[mapping['file']]
            offset = mapping['offset'] + row['address'] - mapping['address']
            header = read_at(stream, offset, 32, mapping['offset'] + mapping['size'])
            magic, cpu, subtype, _, command_count, command_size, _, _ = struct.unpack('<IiiIIIII', header)
            if magic != 0xfeedfacf or not 1 <= command_count <= command_size // 8 or command_size + 32 > row['text_size']:
                raise ValueError('lcer.dyld_cache_invalid')
            architecture = ('arm64e' if subtype & 0x00ffffff == 2 else 'arm64') if cpu == 0x0100000c else 'x86_64' if cpu == 0x01000007 else None
            if architecture is None:
                raise ValueError('lcer.dyld_cache_invalid')
            raw = read_at(stream, offset + 32, command_size, mapping['offset'] + mapping['size'])
            cursor, uuids = 0, []
            for _ in range(command_count):
                if cursor + 8 > len(raw):
                    raise ValueError('lcer.dyld_cache_invalid')
                command, size = struct.unpack_from('<II', raw, cursor)
                if size < 8 or size % 8 or cursor + size > len(raw):
                    raise ValueError('lcer.dyld_cache_invalid')
                if command == 0x1b:
                    if size != 24:
                        raise ValueError('lcer.dyld_cache_invalid')
                    uuids.append(uuid_text(raw[cursor + 8:cursor + 24]))
                cursor += size
            if cursor != len(raw) or uuids != [row['macho_uuid']]:
                raise ValueError('lcer.dyld_cache_invalid')
            images.append({'realpath': row['realpath'], 'sha256': main['sha256'],
                           'macho_uuid': row['macho_uuid'], 'architecture': architecture, 'source': 'dyld_shared_cache'})
    finally:
        for stream in streams.values():
            stream.close()
    if len({row['realpath'] for row in images}) != len(images):
        raise ValueError('lcer.dyld_cache_invalid')
    for file in files:
        if external_file_identity(file['realpath']) != file:
            raise ValueError('lcer.external_input_changed')
    return {'main': main, 'files': files, 'cache_uuids': cache_uuids,
            'images': sorted(images, key=lambda row: row['realpath'])}


def reconcile_process_images(reported, mapped_paths, cache, process_architecture):
    """Derive rows from actual mapped paths and independently read image bytes."""
    fields = {'realpath', 'sha256', 'macho_uuid', 'architecture', 'source'}
    if (process_architecture not in ('arm64', 'arm64e', 'x86_64') or
            any(type(row) is not dict or set(row) != fields for row in reported) or
            len({row['realpath'] for row in reported}) != len(reported) or
            len(set(mapped_paths)) != len(mapped_paths) or
            sorted(row['realpath'] for row in reported) != sorted(mapped_paths)):
        raise ValueError('lcer.process_images_invalid')
    family = 'arm64' if process_architecture.startswith('arm64') else 'x86_64'
    cached = {row['realpath']: row for row in cache['images']}
    if len(cached) != len(cache['images']):
        raise ValueError('lcer.process_images_invalid')
    expected = []
    for path in sorted(mapped_paths):
        if path in cached:
            row = cached[path]
            if row['sha256'] != cache['main']['sha256'] or not row['architecture'].startswith(family):
                raise ValueError('lcer.process_images_invalid')
        else:
            choices = [row for row in macho_file_images(path) if row['architecture'].startswith(family)]
            # Do not use the child's claimed UUID to choose an ambiguous fat
            # slice. Only an independently unique compatible image can pass.
            if len(choices) != 1 or choices[0]['realpath'] != path:
                raise ValueError('lcer.process_images_invalid')
            row = choices[0]
        expected.append(row)
    if sorted(reported, key=lambda row: row['realpath']) != expected:
        raise ValueError('lcer.process_images_invalid')
    return expected


class UbtActionArchive:
    """Decode the complete action section of UE 5.8 TargetMakefile v37.

    This reads data only. Command strings and serializer names never execute.
    Later UHT/cache metadata remains opaque and is bound by the file hash.
    """

    def __init__(self, raw):
        self.raw = raw
        self.offset = 0
        self.objects = []

    def take(self, count):
        if type(count) is not int or count < 0 or count > len(self.raw) - self.offset:
            raise ValueError('lcer.build_action_graph_invalid')
        start = self.offset
        self.offset += count
        return self.raw[start:self.offset]

    def integer(self):
        return struct.unpack('<i', self.take(4))[0]

    def byte(self):
        return self.take(1)[0]

    def boolean(self):
        value = self.byte()
        if value not in (0, 1):
            raise ValueError('lcer.build_action_graph_invalid')
        return bool(value)

    def string(self):
        count = self.integer()
        if count == -1:
            return None
        try:
            value = self.take(count).decode('utf-8', 'strict')
        except UnicodeError as error:
            raise ValueError('lcer.build_action_graph_invalid') from error
        if '\0' in value:
            raise ValueError('lcer.build_action_graph_invalid')
        return value

    def sequence(self, reader):
        count = self.integer()
        if count == -1:
            return None
        if count < 0 or count > len(self.raw) - self.offset:
            raise ValueError('lcer.build_action_graph_invalid')
        return [reader() for _ in range(count)]

    def reference(self, kind):
        index = self.integer()
        if index == -1:
            return None
        if not 0 <= index <= len(self.objects):
            raise ValueError('lcer.build_action_graph_invalid')
        if index == len(self.objects):
            value = self.string()
            if value is None:
                raise ValueError('lcer.build_action_graph_invalid')
            self.objects.append((kind, value))
        observed_kind, value = self.objects[index]
        if observed_kind != kind:
            raise ValueError('lcer.build_action_graph_invalid')
        return value

    def file_item(self):
        return self.reference('file')

    def directory_item(self):
        return self.reference('directory')

    def config_dependency(self):
        key = [self.integer(), self.string(), self.string(), self.string(), self.string()]
        return {'key': key, 'values': self.sequence(self.string)}

    def target_info(self):
        return [self.string(), self.string(), self.string(), self.sequence(self.string),
                self.string(), self.sequence(self.string), self.string()]

    def action(self):
        serializer = self.reference('serializer')
        if serializer not in ('DefaultActionSerializer', 'ClangSpecificFileActionSerializer'):
            raise ValueError('lcer.build_action_serializer_unclassified')
        result = {'type': self.byte(), 'artifact_mode': self.byte(), 'cwd': self.string(),
                  'command': self.string(), 'arguments': self.string(), 'response_contents': self.sequence(self.string),
                  'version': self.string(), 'description': self.string(), 'status': self.string()}
        result['flags'] = [self.boolean() for _ in range(11)]
        for name in ('prerequisites', 'produced', 'deleted'):
            result[name] = self.sequence(self.file_item)
        result['root_names'] = self.sequence(lambda: [self.integer(), self.string()])
        result['root_directories'] = self.sequence(lambda: [self.integer(), self.directory_item()])
        result['root_extras'] = self.sequence(lambda: [self.string(), self.directory_item()])
        result['root_use_vfs'] = self.boolean()
        result['dependency_list'] = self.file_item()
        result['use_history'] = self.boolean()
        result['high_priority'] = self.boolean()
        result['weight'] = struct.unpack('<d', self.take(8))[0]
        result['cache_bucket'] = struct.unpack('<I', self.take(4))[0]
        result['serializer'] = serializer
        if serializer == 'ClangSpecificFileActionSerializer':
            result['specific_file_source_directory'] = self.directory_item()
            result['specific_file_output_directory'] = self.directory_item()
            result['specific_file_response_lines'] = self.sequence(self.string)
        if (not result['cwd'] or not Path(result['cwd']).is_absolute() or not result['command'] or
                not Path(result['command']).is_absolute() or result['arguments'] is None or
                any(result[name] is None for name in ('prerequisites', 'produced', 'deleted')) or
                any(path is None or not Path(path).is_absolute() for name in ('prerequisites', 'produced', 'deleted')
                    for path in result[name])):
            raise ValueError('lcer.build_action_graph_invalid')
        return result

    def actions(self):
        if self.offset != 0 or self.integer() != 37 or self.boolean():
            raise ValueError('lcer.build_action_graph_invalid')
        created_ticks = struct.unpack('<q', self.take(8))[0]
        diagnostics = self.sequence(self.string)
        external_metadata = self.string()
        executable, receipt, intermediate, intermediate_no_arch = [self.string() for _ in range(4)]
        target_type, test_target = self.integer(), self.boolean()
        config_dependencies = self.sequence(self.config_dependency)
        deploy = self.boolean()
        lists = [self.sequence(self.string) for _ in range(6)]
        targets = self.sequence(self.target_info)
        logs = self.sequence(lambda: self.take(self.integer()))
        actions = self.sequence(self.action)
        if not actions:
            raise ValueError('lcer.build_action_graph_invalid')
        return {'version': 37, 'created_ticks': created_ticks, 'diagnostics': diagnostics,
                'external_metadata': external_metadata, 'executable': executable, 'receipt': receipt,
                'intermediate': intermediate, 'intermediate_no_arch': intermediate_no_arch,
                'target_type': target_type, 'test_target': test_target, 'config_dependencies': config_dependencies,
                'deploy': deploy, 'plugin_argument_script_lists': lists, 'prebuild_targets': targets,
                'log_bytes_sha256': [hashlib.sha256(raw).hexdigest() for raw in (logs or [])],
                'actions': actions, 'action_section_end_offset': self.offset,
                'archive_sha256': hashlib.sha256(self.raw).hexdigest()}


def clang_dependency_paths(raw):
    """Read Clang's emitted Make dependency rule without evaluating Make."""
    text = raw.decode('utf-8', 'strict')
    tokens = []
    current = ''
    index = 0
    while index < len(text):
        character = text[index]
        if character == '\\':
            index += 1
            if index == len(text):
                raise ValueError('lcer.build_dependencies_invalid')
            if text[index] == '\n':
                if current:
                    tokens.append(current); current = ''
            else:
                current += text[index]
        elif character == '$':
            if index + 1 == len(text) or text[index + 1] != '$':
                raise ValueError('lcer.build_dependencies_invalid')
            current += '$'; index += 1
        elif character in ' \t\r\n:':
            if current:
                tokens.append(current); current = ''
            if character == ':':
                tokens.append(':')
        elif character == '#' or character == '\0':
            raise ValueError('lcer.build_dependencies_invalid')
        else:
            current += character
        index += 1
    if current:
        tokens.append(current)
    if tokens.count(':') != 1:
        raise ValueError('lcer.build_dependencies_invalid')
    separator = tokens.index(':')
    if not separator or separator == len(tokens) - 1:
        raise ValueError('lcer.build_dependencies_invalid')
    return tokens[:separator], tokens[separator + 1:]


def build_action_prerequisites(archive, log_raw, dependency_reader=None):
    """Follow the actual receipt's producing actions and each prerequisite.

    Preserve the full archive separately. Unused compiler templates have no
    produced artifact and cannot substitute for an executed compile action.
    """
    actions = archive['actions']
    producer = {}
    for index, action in enumerate(actions):
        for output in action['produced']:
            if output in producer:
                raise ValueError('lcer.build_action_graph_invalid')
            producer[output] = index
    root = archive['receipt']
    if root not in producer:
        raise ValueError('lcer.build_action_graph_invalid')
    selected = set()
    active = set()

    def visit(index):
        if index in active:
            raise ValueError('lcer.build_action_graph_invalid')
        if index in selected:
            return
        active.add(index)
        for path in actions[index]['prerequisites']:
            if path in producer:
                visit(producer[path])
        active.remove(index)
        selected.add(index)

    visit(producer[root])
    recorded = []
    lines = log_raw.decode('utf-8', 'strict').splitlines()
    for line in lines:
        match = re.fullmatch(r'\[(\d+)/(\d+)\] (.+)', line)
        if re.match(r'^\[\d', line) and match is None:
            raise ValueError('lcer.build_execution_log_invalid')
        if match:
            label = match[3]
            if label.endswith(' [NoUba]'):
                label = label[:-8]
                if not any(not actions[i]['flags'][3] and
                           actions[i]['description'] + ' ' + actions[i]['status'] == label for i in selected):
                    raise ValueError('lcer.build_execution_log_invalid')
            recorded.append((int(match[1]), int(match[2]), label))
    if recorded:
        totals = {row[1] for row in recorded}
        if len(totals) != 1 or sorted(row[0] for row in recorded) != list(range(1, recorded[0][1] + 1)):
            raise ValueError('lcer.build_execution_log_invalid')
    available = Counter(actions[i]['description'] + ' ' + actions[i]['status'] for i in selected)
    observed = Counter(row[2] for row in recorded)
    if observed - available or [line for line in lines if line.startswith('Result:')] != ['Result: Succeeded']:
        raise ValueError('lcer.build_execution_log_invalid')
    paths = set()
    for index in sorted(selected):
        action = actions[index]
        paths.add(action['command'])
        paths.update(action['prerequisites'])
        dependency = action['dependency_list']
        if dependency is not None:
            paths.add(dependency)
            raw = Path(dependency).read_bytes() if dependency_reader is None else dependency_reader(dependency)
            targets, inputs = clang_dependency_paths(raw)
            actual_targets = [str((Path(action['cwd']) / path).absolute()) if not Path(path).is_absolute() else path for path in targets]
            if not set(actual_targets) <= set(action['produced']):
                raise ValueError('lcer.build_dependencies_invalid')
            for path in inputs:
                paths.add(str((Path(action['cwd']) / path).absolute()))
    return {'action_indices': sorted(selected), 'executed_action_count': len(recorded),
            'prerequisite_paths': sorted(paths)}


def ubt_response_arguments(raw):
    """Decode the observed UBT response-file subset without invoking a shell.

    UBT's emitted files here use whitespace and double quotes. Reject escape,
    single-quote and nested-response forms until their semantics are covered;
    do not silently apply shell rules to Clang or .NET argument strings.
    """
    try:
        value = raw.decode('utf-8', 'strict')
    except UnicodeError as error:
        raise ValueError('lcer.build_response_invalid') from error
    if any(character in value for character in ('\0', '\\', "'", '\ufeff')):
        raise ValueError('lcer.build_response_invalid')
    result, current, quoted, present = [], '', False, False
    for character in value:
        if character == '"':
            quoted = not quoted
            present = True
        elif character in ' \t\r\n' and not quoted:
            if present:
                result.append(current)
            current, present = '', False
        else:
            current += character
            present = True
    if quoted:
        raise ValueError('lcer.build_response_invalid')
    if present:
        result.append(current)
    for index, value in enumerate(result):
        if not value.startswith('@'):
            continue
        previous = result[index - 1] if index else None
        linker_value = ((previous == '-rpath' and value.startswith(('@loader_path/', '@executable_path/')))
                        or (previous == '-install_name' and re.fullmatch(r'@rpath/[A-Za-z0-9_.-]+\.dylib', value)))
        if not linker_value:
            raise ValueError('lcer.build_response_invalid')
    return result


def parse_ubt_receipt(raw):
    """Read Unreal's external JSON receipt without imposing CITY wire spacing."""
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('lcer.build_receipt_invalid')
            result[key] = value
        return result

    def constant(_):
        raise ValueError('lcer.build_receipt_invalid')

    def floating(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError('lcer.build_receipt_invalid')
        return value

    if type(raw) is not bytes:
        raise ValueError('lcer.build_receipt_invalid')
    try:
        value = json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=unique,
                           parse_constant=constant, parse_float=floating)
        if type(value) is not dict:
            raise ValueError('lcer.build_receipt_invalid')
        return value
    except (UnicodeError, ValueError, TypeError, RecursionError) as error:
        raise ValueError('lcer.build_receipt_invalid') from error


class BuildActionInputInventory:
    """Read a target's actual archive, response files, receipt and inputs.

    A disk inventory is not invocation provenance. ``from_workspace`` also
    binds the reader to the acquisition owner's successful captured build.
    Neither route grants source-audit or live-world acceptance.
    """

    def __init__(self, archive_path, log_raw, project, engine_root, editor, target_name):
        self._project_root = Path(project).absolute().parent
        self._files, self._aliases = {}, {}
        self._workspace = None
        self._capture_raw = None
        self._invocation_log = None
        self._project = self._pin(project)
        self._editor = self._pin(editor)
        self._engine_root = Path(engine_root).resolve(strict=True)
        if (not self._engine_root.is_dir() or not self._project_root.is_dir()
                or not isinstance(target_name, str) or re.fullmatch('[A-Za-z0-9_]+Editor', target_name) is None):
            raise ValueError('lcer.build_target_invalid')
        expected = self._project_root / 'Intermediate/Build/Mac/arm64' / target_name / 'Development/Makefile.bin'
        if Path(archive_path).absolute() != expected:
            raise ValueError('lcer.build_target_invalid')
        graph = UbtActionArchive(self._read(expected)).actions()
        self._archive = self._pin(expected)
        receipt_path = self._project_root / 'Binaries/Mac' / (target_name + '.target')
        if (graph['receipt'] != str(receipt_path) or graph['target_type'] != 1 or graph['test_target']
                or graph['intermediate'] != str(expected.parent)
                or graph['intermediate_no_arch'] != str(self._project_root / 'Intermediate/Build/Mac' / target_name / 'Development')):
            raise ValueError('lcer.build_target_invalid')
        executable = self._pin(graph['executable'])
        # Pin depfiles before the closure walker reads their contents. Verify
        # again after all dependent reads, including realpath alias resolution.
        closure = build_action_prerequisites(graph, log_raw, self._read)
        selected = [graph['actions'][index] for index in closure['action_indices']]
        for path in closure['prerequisite_paths']:
            self._pin(path)
        compilers, sdks, linked = {}, {}, set()
        for action in selected:
            if action['type'] == 7:
                # WriteMetadata runs a .NET program. The program DLL is an
                # argument rather than a FileItem prerequisite in this graph.
                match = re.fullmatch(r'"([^"\\\x00\r\n]+)" -Session="\{[0-9a-fA-F-]{36}\}" '
                                     r'-Mode=WriteMetadata -Input="([^"\\\x00\r\n]+)" -Version=2', action['arguments'])
                if (match is None or Path(action['command']).name != 'dotnet'
                        or match[1] != str(self._engine_root / 'Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll')
                        or match[2] not in action['prerequisites']):
                    raise ValueError('lcer.build_metadata_action_invalid')
                self._pin(match[1])
                self._pin(match[2])
                continue
            if action['type'] not in (3, 6):
                raise ValueError('lcer.build_action_unclassified')
            if Path(action['command']).name not in ('clang', 'clang++'):
                raise ValueError('lcer.build_toolchain_invalid')
            compiler = self._pin(action['command'])
            compilers[compiler['realpath']] = compiler
            match = re.fullmatch(r'@"([^"\\\x00\r\n]+)"', action['arguments'])
            if match is None or match[1] not in action['prerequisites'] or not Path(match[1]).is_absolute():
                raise ValueError('lcer.build_response_invalid')
            argv = ubt_response_arguments(self._read(match[1]))
            if any((Path(action['cwd']) / value[1:]).is_file() for value in argv if value.startswith('@')):
                # Clang can expand an existing response file even where a
                # linker path was intended. The literal's spelling alone is
                # insufficient if that external response target exists.
                raise ValueError('lcer.build_response_invalid')
            archived = action['response_contents']
            if (type(archived) is not list or any(type(line) is not str for line in archived)
                    or argv != ubt_response_arguments('\n'.join(archived).encode('utf-8'))):
                raise ValueError('lcer.build_response_changed')
            # These are the emitted MacToolChain flags, not values guessed
            # from compiler installation directories or the child's report.
            if (argv.count('-arch') != 1 or argv.count('-isysroot') != 1
                    or any(value.startswith('--sysroot') or (value.startswith('-isysroot') and value != '-isysroot')
                           for value in argv)):
                raise ValueError('lcer.build_toolchain_invalid')
            arch_at, sdk_at = argv.index('-arch'), argv.index('-isysroot')
            if (arch_at + 1 == len(argv) or argv[arch_at + 1] != 'arm64'
                    or sdk_at + 1 == len(argv) or not Path(argv[sdk_at + 1]).is_absolute()):
                raise ValueError('lcer.build_toolchain_invalid')
            sdk = self._pin(Path(argv[sdk_at + 1]) / 'SDKSettings.json')
            sdks[sdk['realpath']] = sdk
            if action['type'] == 6:
                linked.update(str(Path(path).resolve(strict=True)) for path in action['produced'] if path.endswith('.dylib'))
        if len(compilers) != 1 or len(sdks) != 1:
            raise ValueError('lcer.build_toolchain_invalid')
        receipt = parse_ubt_receipt(self._read(receipt_path))
        expected_fields = {'TargetName': target_name, 'Platform': 'Mac', 'Configuration': 'Development',
                           'TargetType': 'Editor', 'Architecture': 'arm64', 'IsTestTarget': False}
        if (type(receipt) is not dict or any(type(receipt.get(key)) is not type(value) or receipt[key] != value
                                           for key, value in expected_fields.items())
                or type(receipt.get('Project')) is not str
                or self._pin(receipt_path.parent / receipt['Project']) != self._project):
            raise ValueError('lcer.build_receipt_invalid')
        if self._pin(self._receipt_path(receipt.get('Launch'))) != self._editor:
            raise ValueError('lcer.build_receipt_invalid')
        products = receipt.get('BuildProducts')
        if type(products) is not list or not products:
            raise ValueError('lcer.build_receipt_invalid')
        seen, modules = set(), []
        for product in products:
            if (type(product) is not dict or type(product.get('Path')) is not str
                    or product.get('Type') not in ('Executable', 'DynamicLibrary', 'StaticLibrary',
                                                  'ImportLibrary', 'SymbolFile', 'RequiredResource', 'BuildResource', 'MapFile')):
                raise ValueError('lcer.build_receipt_invalid')
            path = self._receipt_path(product['Path'])
            if path in seen:
                raise ValueError('lcer.build_receipt_invalid')
            seen.add(path)
            if Path(path).is_relative_to(self._project_root) and product['Type'] == 'DynamicLibrary':
                identity = self._pin(path)
                if identity['realpath'] not in linked:
                    raise ValueError('lcer.build_module_producer_missing')
                images = [image for image in macho_file_images(path) if image['architecture'] == 'arm64']
                if len(images) != 1 or images[0]['sha256'] != identity['sha256']:
                    raise ValueError('lcer.image_identity_invalid')
                modules.append(images[0])
        # Link stubs remain input artifacts. Every linked library in the
        # project's final Binaries directories must appear in the receipt.
        final = {path for path in linked if Path(path).is_relative_to(self._project_root)
                 and 'Binaries' in Path(path).relative_to(self._project_root).parts}
        if (not modules or final != {row['realpath'] for row in modules}
                or graph['executable'] not in seen):
            raise ValueError('lcer.build_module_producer_missing')
        self._result = {'engine_root': str(self._engine_root),
                        'engine_build_version': self._pin(self._engine_root / 'Build/Build.version'),
                        'compiler': next(iter(compilers.values())), 'sdk': next(iter(sdks.values())),
                        'editor': self._editor, 'project': self._project,
                        'target_executable': executable,
                        'modules': sorted(modules, key=lambda row: row['realpath']),
                        'archive': self._archive, 'receipt': self._pin(receipt_path),
                        'action_indices': closure['action_indices'],
                        'executed_action_count': closure['executed_action_count']}
        self.verify()

    def _pin(self, path):
        supplied = Path(path)
        if not supplied.is_absolute():
            raise ValueError('lcer.build_input_path_invalid')
        actual = supplied.resolve(strict=True)
        if ((supplied.is_relative_to(self._project_root) or actual.is_relative_to(self._project_root))
                and any(item.is_symlink() for item in [supplied, *supplied.parents])):
            raise ValueError('lcer.dependency_path_invalid')
        record = external_file_identity(supplied)
        alias = str(supplied)
        if (self._aliases.setdefault(alias, record['realpath']) != record['realpath']
                or self._files.setdefault(record['realpath'], record) != record):
            raise ValueError('lcer.external_input_changed')
        return dict(record)

    def _read(self, path):
        record = self._pin(path)
        raw = Path(record['realpath']).read_bytes()
        if len(raw) != record['size_bytes'] or hashlib.sha256(raw).hexdigest() != record['sha256']:
            raise ValueError('lcer.external_input_changed')
        return raw

    def _receipt_path(self, value):
        if type(value) is not str or not value or '\0' in value:
            raise ValueError('lcer.build_receipt_invalid')
        for prefix, root in (('$(EngineDir)', self._engine_root), ('$(ProjectDir)', self._project_root)):
            if value[:len(prefix)].lower() == prefix.lower():
                tail = value[len(prefix):]
                if not tail.startswith('/') or '..' in Path(tail).parts or '$(' in tail:
                    raise ValueError('lcer.build_receipt_invalid')
                return str(root / tail[1:])
        if not Path(value).is_absolute() or '$(' in value or '..' in Path(value).parts:
            raise ValueError('lcer.build_receipt_invalid')
        return value

    def verify(self):
        if self._workspace is not None:
            self._workspace.verify()
            if stored_json_bytes(self._workspace._build_capture) != self._capture_raw:
                raise ValueError('lcer.build_capture_changed')
            if external_file_identity(self._invocation_log['realpath']) != self._invocation_log:
                raise ValueError('lcer.build_capture_changed')
            if current_python_runtime() != parse_stored_json(self._capture_raw)['python_runtime']:
                raise ValueError('lcer.python_runtime_changed')
        for alias, expected in self._aliases.items():
            if str(Path(alias).resolve(strict=True)) != expected:
                raise ValueError('lcer.external_input_changed')
        for path, record in self._files.items():
            if external_file_identity(path) != record:
                raise ValueError('lcer.external_input_changed')

    def snapshot(self):
        self.verify()
        return parse_stored_json(stored_json_bytes({**self._result,
            'build_inputs': [self._files[path] for path in sorted(self._files)]}))

    @classmethod
    def from_workspace(cls, workspace):
        if not isinstance(workspace, AcquisitionWorkspace) or not workspace._reserved:
            raise ValueError('lcer.operation_sequence_invalid')
        workspace.verify()
        if workspace._build_capture is None:
            raise ValueError('lcer.build_capture_missing')
        capture_raw = stored_json_bytes(workspace._build_capture)
        captured = parse_stored_json(capture_raw)
        if captured['returncode'] != 0:
            raise ValueError('lcer.build_capture_missing')
        policy = workspace._plan['constitutional_policy']
        project = workspace._repository_root / policy['runtime']['project']
        expected_argv = [value.format(absolute_city_project=str(project)) for value in policy['build_argv']]
        log_path = workspace._output_root / 'build.log'
        log = external_file_identity(log_path)
        log_raw = log_path.read_bytes()
        python_runtime, compiler_log = python_runtime_from_build_log(workspace._contract_raw, log_raw)
        if (captured['argv'] != expected_argv or captured['cwd'] != str(workspace._repository_root)
                or captured['source_files'] != workspace._source_snapshot
                or captured.get('python_runtime') != python_runtime or current_python_runtime() != python_runtime
                or captured['log'] != {'path': 'build.log', 'sha256': log['sha256'], 'size_bytes': log['size_bytes']}):
            raise ValueError('lcer.build_capture_changed')
        archive = project.parent / 'Intermediate/Build/Mac/arm64' / expected_argv[1] / 'Development/Makefile.bin'
        result = cls(archive, compiler_log, project, Path(expected_argv[0]).parents[3],
                     policy['runtime']['engine'], expected_argv[1])
        if external_file_identity(log_path) != log:
            raise ValueError('lcer.build_capture_changed')
        result._workspace = workspace
        result._capture_raw = capture_raw
        result._invocation_log = log
        result._result['python'] = python_runtime['executable']
        result._result['python_runtime'] = python_runtime
        result.verify()
        return result


class RuntimeBuildInputInventory:
    """Join observed runtime inputs to pinned build files and cache bytes.

    The caller must supply original process observations. This checks their
    input identities, not their process/pipe provenance or world semantics.
    A standalone metadata fixture does not become a captured build here.
    """

    def __init__(self, contract_raw, build, cache_path, python_runtime, proof_module_path):
        if not isinstance(build, BuildActionInputInventory):
            raise ValueError('lcer.build_input_inventory_missing')
        self.validator = FrozenWireValidator(contract_raw)
        self._build = build
        self._build_raw = stored_json_bytes(build.snapshot())
        self._python_raw = stored_json_bytes(python_runtime)
        if current_python_runtime() != python_runtime:
            raise ValueError('lcer.python_runtime_changed')
        native = parse_stored_json(self._build_raw)
        modules = [row for row in native['modules'] if row['realpath'] == str(proof_module_path)]
        if len(modules) != 1:
            raise ValueError('lcer.proof_module_identity_invalid')
        self._proof_module_raw = stored_json_bytes(modules[0])
        self._cache_raw = stored_json_bytes(dyld_cache_inventory(cache_path))
        self._cache_process_raw = None
        self._platform_raw = None
        self._native_parents_raw = None
        self._native_parents_sha256 = None
        self._launches = {}
        self._failed = False
        self.verify()

    @property
    def cache(self):
        return parse_stored_json(self._cache_raw)

    def verify(self):
        try:
            self._verify_files()
        except BaseException:
            self._failed = True
            raise

    def _verify_files(self):
        if self._build.snapshot() != parse_stored_json(self._build_raw):
            raise ValueError('lcer.build_input_inventory_changed')
        if current_python_runtime() != parse_stored_json(self._python_raw):
            raise ValueError('lcer.python_runtime_changed')
        for file in parse_stored_json(self._cache_raw)['files']:
            if external_file_identity(file['realpath']) != file:
                raise ValueError('lcer.external_input_changed')
        if self._cache_process_raw is not None and current_dyld_process() != parse_stored_json(self._cache_process_raw):
            raise ValueError('lcer.dyld_cache_observation_changed')
        if self._platform_raw is not None:
            platform = parse_stored_json(self._platform_raw)
            for file in platform['engine_configs'] + platform['engine_plugins']:
                if external_file_identity(file['realpath']) != file:
                    raise ValueError('lcer.external_input_changed')
            reconcile_process_images(platform['loaded_images'], [row['realpath'] for row in platform['loaded_images']],
                                     parse_stored_json(self._cache_raw), 'arm64')

    def validate_observation(self, observation):
        if self._failed:
            raise ValueError('lcer.runtime_input_inventory_failed')
        # Any failed input sample terminates this acquisition's inventory.
        # Restoring bytes afterwards must not reopen an acceptance route.
        self._failed = True
        self.verify()
        observation = parse_stored_json(stored_json_bytes(observation))
        self.validator.validate('process_observation', observation)
        startup = observation['startup']
        native = parse_stored_json(self._build_raw)
        if (observation['executable'] != native['editor'] or startup['pid'] != observation['pid']
                or startup['cwd_realpath'] != observation['cwd_realpath']
                or observation['loaded_images'] != startup['loaded_images']
                or startup['proof_module'] != parse_stored_json(self._proof_module_raw)):
            raise ValueError('lcer.runtime_build_identity_mismatch')
        platform = {}
        for source, destination in (('config_files', 'engine_configs'), ('enabled_plugins', 'engine_plugins')):
            files = startup[source]
            paths = [file['realpath'] for file in files]
            if not paths or paths != sorted(set(paths)):
                raise ValueError('lcer.runtime_input_inventory_invalid')
            for file in files:
                if external_file_identity(file['realpath']) != file:
                    raise ValueError('lcer.runtime_input_inventory_invalid')
            platform[destination] = files
        images = reconcile_process_images(startup['loaded_images'],
            [row['realpath'] for row in observation['loaded_images']], parse_stored_json(self._cache_raw), 'arm64')
        if (images != observation['loaded_images'] or any(module not in images for module in native['modules'])
                or native['editor']['realpath'] not in {row['realpath'] for row in images}):
            raise ValueError('lcer.runtime_build_identity_mismatch')
        platform['loaded_images'] = images
        raw = stored_json_bytes(platform)
        if self._platform_raw is not None and self._platform_raw != raw:
            raise ValueError('lcer.runtime_input_inventory_changed')
        identity = stored_json_bytes({key: observation[key] for key in ('pid', 'ppid', 'macos_birth_tuple')})
        binding = (startup['witness_id'], startup['domain'], identity)
        if startup['launch_id'] in self._launches and self._launches[startup['launch_id']] != binding:
            raise ValueError('lcer.original_process_identity_mismatch')
        self._platform_raw = raw
        self.verify()
        self._launches[startup['launch_id']] = binding
        self._failed = False

    def require_launches(self, launches):
        if self._failed:
            raise ValueError('lcer.runtime_input_inventory_failed')
        expected = [(row['witness_id'], row['domain'], row['launch_id']) for row in launches]
        actual = [(value[0], value[1], key) for key, value in self._launches.items()]
        if len(expected) != len(set(expected)) or sorted(expected) != sorted(actual):
            raise ValueError('lcer.runtime_input_launches_incomplete')
        self.verify()

    def external_inputs(self):
        if self._failed or self._platform_raw is None:
            raise ValueError('lcer.runtime_input_inventory_incomplete')
        self.verify()
        native = parse_stored_json(self._build_raw)
        cache = parse_stored_json(self._cache_raw)
        files = {}
        for file in native['build_inputs'] + cache['files']:
            if files.setdefault(file['realpath'], file) != file:
                raise ValueError('lcer.external_input_changed')
        result = {key: native[key] for key in ('engine_root', 'engine_build_version', 'compiler', 'sdk')}
        result.update(python=parse_stored_json(self._python_raw)['executable'],
                      build_inputs=[files[path] for path in sorted(files)], dyld_cache=cache['main'],
                      **parse_stored_json(self._platform_raw))
        self.validator.validate('external_inputs', result)
        return result

    def native_class_parents(self):
        """Decode ancestry from this build and its observed loaded images.

        The cold native decoder reads bound bytes. It supplies no world counts,
        owner, generation or acceptance decision. Parent world checks and the
        independent release verifier separately derive those from raw rows.
        """
        external = self.external_inputs()
        self._failed = True
        if self._native_parents_raw is None:
            # This is one of the six declared local modules. Restore the closed
            # harness import path after the verifier's stdlib-only bootstrap.
            _prepare_source_imports()
            from verify_live_cross_domain_evidence_round_trip_release import ExternalFileSnapshot, native_class_inventory
            _prepare_source_imports()
            files = ExternalFileSnapshot(external['build_inputs'])
            images = [row for row in external['loaded_images'] if row['source'] == 'dyld']
            layout = str(Path(external['engine_root']) / 'Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h')
            registry = native_class_inventory(files, images, external['build_inputs'], layout)
            policy = FrozenObligationPlanCompiler(self.validator._contract_raw).compile()['constitutional_policy']
            parents = registry.require_classes([policy['runtime']['game_mode'],
                '/Script/CityLiveEvidenceProof.CityLiveEvidenceActor', '/Script/Engine.Actor',
                '/Script/Engine.Pawn', '/Script/Engine.Controller'])
            self._native_parents_raw = stored_json_bytes(parents)
            self._native_parents_sha256 = hashlib.sha256(self._native_parents_raw).hexdigest()
        if hashlib.sha256(self._native_parents_raw).hexdigest() != self._native_parents_sha256:
            raise ValueError('lcer.native_ancestry_invalid')
        # Re-reading the build, config, cache and image identities is mandatory
        # even when the expensive native decoder's unchanged result is cached.
        self.verify()
        result = parse_stored_json(self._native_parents_raw)
        self._failed = False
        return result

    @classmethod
    def from_workspace(cls, workspace):
        build = BuildActionInputInventory.from_workspace(workspace)
        native = build.snapshot()
        cache = current_dyld_cache()
        policy = workspace._plan['constitutional_policy']['runtime']
        module = policy['game_mode'].split('.', 1)[0].rsplit('/', 1)[-1]
        proof_module = workspace._repository_root / policy['plugin'] / 'Binaries/Mac' / ('libUnrealEditor-' + module + '.dylib')
        result = cls(workspace._contract_raw, build, cache['inventory']['main']['realpath'],
                     native['python_runtime'], proof_module)
        if result.cache != cache['inventory']:
            raise ValueError('lcer.dyld_cache_observation_changed')
        result._cache_process_raw = stored_json_bytes(cache['process'])
        result.verify()
        return result


def parse_lsof_descriptors(raw, pid):
    """Parse the explicit NUL-field format; paths may contain spaces/newlines."""
    rows = []
    process = None
    current = None
    for field in raw.split(b"\0"):
        # lsof inserts a record LF before the first field of the next record.
        if field.startswith(b"\n"):
            field = field[1:]
        if not field:
            continue
        tag, value = field[:1], field[1:].decode("utf-8", "strict")
        if tag == b"p":
            if process is not None or not value.isdecimal() or int(value) != pid:
                raise ValueError("lcer.process_observation_invalid")
            process = int(value)
        elif tag == b"f":
            if process is None or not value.isdecimal():
                raise ValueError("lcer.process_observation_invalid")
            current = {"fd": int(value)}
            rows.append(current)
        elif tag in (b"a", b"t", b"n", b"d"):
            name = {b"a": "access", b"t": "type", b"n": "name", b"d": "device"}[tag]
            if current is None or name in current:
                raise ValueError("lcer.process_observation_invalid")
            current[name] = value
        else:
            raise ValueError("lcer.process_observation_invalid")
    if process != pid or len({row["fd"] for row in rows}) != len(rows):
        raise ValueError("lcer.process_observation_invalid")
    return sorted(rows, key=lambda row: row["fd"])


def vmmap_image_paths(raw, pid, ppid, executable):
    """Extract actual executable mappings from a bound vmmap process report."""
    text = raw.decode('utf-8', 'strict')
    headers = {}
    mappings = []
    sections = []
    collecting = False
    for line in text.splitlines():
        if line.startswith('==== '):
            expected = ['==== Non-writable regions for process %d' % pid,
                        '==== Writable regions for process %d' % pid,
                        '==== Legend', '==== Summary for process %d' % pid]
            if len(sections) >= len(expected) or line != expected[len(sections)]:
                raise ValueError('lcer.process_images_invalid')
            sections.append(line)
            collecting = len(sections) <= 2
        for name in ('Process', 'Parent Process', 'Path', 'Load Address', 'Target Type', 'Analysis Tool'):
            if line.startswith(name + ':'):
                if name in headers:
                    raise ValueError('lcer.process_images_invalid')
                headers[name] = line[len(name) + 1:].strip()
        if collecting and line.startswith('__TEXT'):
            match = re.fullmatch(r'__TEXT(?:_EXEC)?\s+([0-9a-f]+)-([0-9a-f]+)\s+\[[^\]]+\]\s+\S+\s+SM=\S+\s+(/.+)', line)
            if match is None or int(match[1], 16) >= int(match[2], 16):
                raise ValueError('lcer.process_images_invalid')
            mappings.append((int(match[1], 16), int(match[2], 16), match[3]))
    display_path = headers.get('Path', '')
    load_address = headers.get('Load Address', '')
    if (not headers.get('Process', '').endswith(' [%d]' % pid) or
            not headers.get('Parent Process', '').endswith(' [%d]' % ppid) or
            not display_path.startswith('/') or
            (display_path != executable and '*' not in display_path.split('/')) or
            re.fullmatch(r'0x[0-9a-fA-F]+', load_address) is None or
            headers.get('Target Type') != 'live task' or
            headers.get('Analysis Tool') != '/usr/bin/vmmap' or not mappings or len(sections) != 4):
        raise ValueError('lcer.process_images_invalid')
    ranges = sorted(mappings)
    if any(left[1] > right[0] for left, right in zip(ranges, ranges[1:])):
        raise ValueError('lcer.process_images_invalid')
    # vmmap can redact components in its display Path header. Never expand
    # that text as a wildcard or use it to select an executable. Bind the
    # exact kernel-observed path to the actual mapping at the main load address.
    main = [row for row in mappings if row[0] == int(load_address, 16)]
    if len(main) != 1 or main[0][2] != executable:
        raise ValueError('lcer.process_images_invalid')
    return sorted({row[2] for row in mappings})


def exact_pipe_holders(expected, observed):
    """Compare actual holder tuples, rejecting even one extra descriptor."""
    def key(row):
        if (row.get('kind') != 'pipe' or type(row.get('pid')) is not int or row['pid'] <= 0 or
                type(row.get('fd')) is not int or row['fd'] < 0 or
                re.fullmatch('[0-9a-f]{16}', row.get('kernel_id', '')) is None):
            raise ValueError('lcer.process_observation_invalid')
        return row['pid'], row['fd'], row['kernel_id']
    wanted = {key(row): row for row in expected}
    actual = {key(row): row for row in observed}
    if len(wanted) != len(expected) or len(actual) != len(observed):
        raise ValueError('lcer.process_observation_invalid')
    if set(actual) - set(wanted):
        raise ValueError('lcer.proof_pipe_extra_holder')
    if actual != wanted:
        raise ValueError('lcer.original_pipe_identity_mismatch')
    return sorted(observed, key=key)


def _launch_string_prefix(raw):
    """Decode the fixed launch prefix; this alone cannot prove its boundary."""
    if type(raw) is not bytes or len(raw) < 12 or (len(raw) - 4) % 8:
        raise ValueError('lcer.process_observation_invalid')
    count = struct.unpack_from('=i', raw)[0]
    if not 0 < count <= len(raw):
        raise ValueError('lcer.process_observation_invalid')
    offset = 4

    def string():
        nonlocal offset
        end = raw.find(b'\0', offset)
        if end < offset:
            raise ValueError('lcer.process_observation_invalid')
        value = raw[offset:end]
        offset = end + 1
        return value

    executable = string()
    if not executable.startswith(b'/'):
        raise ValueError('lcer.process_observation_invalid')
    while offset < len(raw) and raw[offset] == 0:
        offset += 1
    arguments = [string().decode('utf-8', 'strict') for _ in range(count)]
    if not all(arguments):
        raise ValueError('lcer.process_observation_invalid')
    environment = {}
    expected_names = {'HOME', 'LANG', 'LC_ALL', 'LOGNAME', 'PATH', 'TMPDIR', 'USER'}
    for _ in range(len(expected_names)):
        name, separator, value = string().partition(b'=')
        key = name.decode('ascii', 'strict')
        if not separator or key not in expected_names or key in environment:
            raise ValueError('lcer.process_environment_invalid')
        environment[key] = value.decode('utf-8', 'strict')
    padding = (-(offset - 4)) % 8
    if raw[offset:offset + padding] != bytes(padding):
        raise ValueError('lcer.process_environment_invalid')
    offset += padding
    return arguments, environment, offset


def frozen_launch_procargs(raw):
    """Prove the closed launch boundary against the complete Apple suffix.

    XNU's string area contains argv, env and applev. Only their pointer arrays
    have mandatory NULL separators; the returned string area may have no pad
    between env and applev. A complete ordered bootstrap suffix is required,
    so an extra environment key cannot disappear through a name filter.
    """
    arguments, environment, offset = _launch_string_prefix(raw)

    def string():
        nonlocal offset
        end = raw.find(b'\0', offset)
        if end < offset:
            raise ValueError('lcer.process_observation_invalid')
        value = raw[offset:end]
        offset = end + 1
        return value

    hex64 = rb'0x[0-9a-f]{1,16}'
    fields = [(b'pfz', hex64), (b'stack_guard', hex64),
              (b'malloc_entropy', hex64 + b',' + hex64), (b'ptr_munge', hex64),
              (b'main_stack', b','.join([hex64] * 4)),
              (b'executable_file', hex64 + b',' + hex64), (b'dyld_file', hex64 + b',' + hex64),
              (b'executable_cdhash', rb'[0-9a-f]{40}'), (b'executable_boothash', rb'[0-9a-f]{40}'),
              (b'arm64e_abi', rb'os|all'), (b'th_port', rb'0x[0-9a-f]{1,8}'),
              (b'security_config', rb'0x[0-9a-f]{1,8}')]
    for name, pattern in fields:
        if name == b'stack_guard' and raw[offset:].startswith(b'MallocNanoZone='):
            if string() != b'MallocNanoZone=1':
                raise ValueError('lcer.process_environment_invalid')
        if name == b'arm64e_abi' and not raw[offset:].startswith(b'arm64e_abi='):
            continue  # The x86_64 bootstrap has no arm64e entry.
        actual, separator, value = string().partition(b'=')
        if actual != name or not separator or re.fullmatch(pattern, value) is None:
            raise ValueError('lcer.process_environment_invalid')
    # These optional arm64 bootstrap flags follow security_config on the
    # supported macOS 15 host. Their entire literal values and order matter;
    # unknown fields and a second suffix must remain unconsumed and reject.
    for name in (b'dyld_hw_tpro', b'dyld_hw_tpro_pagers'):
        if raw[offset:].startswith(name + b'='):
            if string() != name + b'=1':
                raise ValueError('lcer.process_environment_invalid')
    padding = (-(offset - 4)) % 8
    if len(raw) - offset != padding or raw[offset:] != bytes(padding):
        raise ValueError('lcer.process_environment_invalid')
    return arguments, environment


class MacProcessObserver:
    """Read kernel identities for this parent and its direct children.

    These observations grant no evidence acceptance. Full acquisition must
    reconcile them with retained original handles, lsof and dyld/vmmap data.
    """

    def __init__(self):
        if sys.platform != "darwin" or ctypes.sizeof(ctypes.c_void_p) != 8:
            raise ValueError("lcer.platform_not_supported")
        self._proc = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        self._libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
        self.last_pipe_census = None
        self.last_pipe_exclusivity = None
        self._launch_boundaries = {}
        self._proc.proc_listpids.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_int]
        self._proc.proc_listpids.restype = ctypes.c_int
        self._proc.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
        self._proc.proc_pidinfo.restype = ctypes.c_int
        self._proc.proc_pidfdinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
        self._proc.proc_pidfdinfo.restype = ctypes.c_int
        self._proc.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        self._proc.proc_pidpath.restype = ctypes.c_int
        self._libc.sysctl.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_uint, ctypes.c_void_p,
                                      ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t]
        self._libc.sysctl.restype = ctypes.c_int

    def identity(self, pid):
        if type(pid) is not int or pid <= 0:
            raise ValueError("lcer.process_observation_invalid")
        value = _BsdProcess()
        if (self._proc.proc_pidinfo(pid, 3, 0, ctypes.byref(value), ctypes.sizeof(value)) != ctypes.sizeof(value)
                or value.pid != pid or value.seconds <= 0 or value.microseconds >= 1000000):
            raise ValueError("lcer.process_observation_invalid")
        return {"pid": value.pid, "ppid": value.ppid,
                "macos_birth_tuple": {"seconds": value.seconds, "microseconds": value.microseconds}}

    def _owned(self, pid, expected_birth):
        identity = self.identity(pid)
        if (identity["macos_birth_tuple"] != expected_birth or
                (pid != os.getpid() and identity["ppid"] != os.getpid())):
            raise ValueError("lcer.process_identity_mismatch")
        return identity

    def paths(self, pid, expected_birth):
        self._owned(pid, expected_birth)
        paths = _ProcessPaths()
        executable = ctypes.create_string_buffer(4096)
        if (self._proc.proc_pidinfo(pid, 9, 0, ctypes.byref(paths), ctypes.sizeof(paths)) != ctypes.sizeof(paths)
                or self._proc.proc_pidpath(pid, executable, len(executable)) <= 0):
            raise ValueError("lcer.process_observation_invalid")
        cwd = os.fsdecode(bytes(paths.cwd.path))
        binary = os.fsdecode(executable.value)
        if not cwd.startswith("/") or not binary.startswith("/") or not paths.cwd.info.stat.ino:
            raise ValueError("lcer.process_observation_invalid")
        current = os.stat(cwd)
        if (current.st_ino != paths.cwd.info.stat.ino or current.st_dev != paths.cwd.info.stat.dev
                or str(Path(cwd).resolve()) != cwd):
            raise ValueError("lcer.process_observation_invalid")
        self._owned(pid, expected_birth)
        return {"cwd_realpath": cwd, "executable_realpath": str(Path(binary).resolve())}

    def architecture(self, pid, expected_birth):
        self._owned(pid, expected_birth)
        value = (ctypes.c_int32 * 2)()
        if self._proc.proc_pidinfo(pid, 19, 0, value, ctypes.sizeof(value)) != ctypes.sizeof(value):
            raise ValueError('lcer.process_observation_invalid')
        cpu, subtype = value
        if cpu == 0x0100000c:
            result = 'arm64e' if subtype & 0x00ffffff == 2 else 'arm64'
        elif cpu == 0x01000007:
            result = 'x86_64'
        else:
            raise ValueError('lcer.process_observation_invalid')
        self._owned(pid, expected_birth)
        return result

    def launch_inputs(self, pid, expected_birth):
        """Read current kernel launch strings using a proved exec boundary.

        libSystem consumes and clears bootstrap strings during startup. The
        first read must prove the complete suffix while the child is stopped.
        Later samples read fresh kernel bytes and require the same full launch
        prefix. They never substitute a saved argv/environment observation.
        """
        self._owned(pid, expected_birth)
        key = (pid, expected_birth['seconds'], expected_birth['microseconds'])
        boundary = self._launch_boundaries.get(key)
        if boundary is None:
            state = _BsdProcess()
            if (self._proc.proc_pidinfo(pid, 3, 0, ctypes.byref(state), ctypes.sizeof(state)) != ctypes.sizeof(state)
                    or state.status != 4):  # SSTOP from sys/proc.h
                raise ValueError('lcer.launch_boundary_unobserved')
        maximum = ctypes.c_int()
        size = ctypes.c_size_t(ctypes.sizeof(maximum))
        if self._libc.sysctl((ctypes.c_int * 2)(1, 8), 2, ctypes.byref(maximum), ctypes.byref(size), None, 0) != 0:
            raise ValueError("lcer.process_observation_invalid")
        if maximum.value <= 0 or maximum.value > 16 * 1024 * 1024:
            raise ValueError("lcer.process_observation_invalid")
        buffer = ctypes.create_string_buffer(maximum.value)
        size = ctypes.c_size_t(len(buffer))
        if self._libc.sysctl((ctypes.c_int * 3)(1, 49, pid), 3, buffer, ctypes.byref(size), None, 0) != 0:
            raise ValueError("lcer.process_observation_invalid")
        raw = buffer.raw[:size.value]
        if boundary is None:
            arguments, environment = frozen_launch_procargs(raw)
            _, _, end = _launch_string_prefix(raw)
            boundary = (len(raw), raw[:end])
        else:
            arguments, environment, end = _launch_string_prefix(raw)
            if boundary != (len(raw), raw[:end]):
                raise ValueError('lcer.process_input_invalid')
        self._owned(pid, expected_birth)
        self._launch_boundaries[key] = boundary
        return arguments, environment

    def descriptor_list(self, pid, expected_birth):
        self._owned(pid, expected_birth)
        size = self._proc.proc_pidinfo(pid, 1, 0, None, 0)
        if size <= 0 or size % ctypes.sizeof(_DescriptorInfo):
            raise ValueError("lcer.process_observation_invalid")
        entries = (_DescriptorInfo * (size // ctypes.sizeof(_DescriptorInfo) + 32))()
        actual = self._proc.proc_pidinfo(pid, 1, 0, entries, ctypes.sizeof(entries))
        if actual <= 0 or actual >= ctypes.sizeof(entries) or actual % ctypes.sizeof(_DescriptorInfo):
            raise ValueError("lcer.process_observation_invalid")
        result = [(entry.fd, entry.kind) for entry in entries[:actual // ctypes.sizeof(_DescriptorInfo)]]
        if any(fd < 0 for fd, _ in result) or len({fd for fd, _ in result}) != len(result):
            raise ValueError("lcer.process_observation_invalid")
        self._owned(pid, expected_birth)
        return sorted(result)

    def pipe(self, pid, expected_birth, fd):
        self._owned(pid, expected_birth)
        result = self._pipe_record(pid, fd)
        self._owned(pid, expected_birth)
        return result

    def _pipe_record(self, pid, fd):
        return self._pipe_metadata(pid, fd)[0]

    def _pipe_metadata(self, pid, fd):
        # Pipe metadata only. The global holder census calls this for holders
        # discovered by kernel enumeration; it cannot read their argv/environment or signal.
        if type(fd) is not int or fd < 0:
            raise ValueError("lcer.process_observation_invalid")
        pipe = _PipeInfo()
        if (self._proc.proc_pidfdinfo(pid, fd, 6, ctypes.byref(pipe), ctypes.sizeof(pipe)) != ctypes.sizeof(pipe)
                or not pipe.handle or pipe.file.type != 6 or pipe.file.flags & 3 not in (1, 2, 3)):
            raise ValueError("lcer.process_observation_invalid")
        row = {"pid": pid, "fd": fd, "kind": "pipe", "kernel_id": "%016x" % pipe.handle,
               "peer_kernel_id": "%016x" % pipe.peer if pipe.peer else None,
               "access": {1: "read", 2: "write", 3: "read_write"}[pipe.file.flags & 3], "path": None}
        return row, pipe.file.status

    def exclusive_pipe_holders(self, endpoints, births):
        """Observe unique original endpoints through the documented sharing bit.

        PROC_FP_SHARED reports additional fileglob references, including dup,
        fork, SCM_RIGHTS and fileports. No inaccessible PID is treated as an
        absent holder. Each supplied endpoint must still exist, retain its
        identity and have no extra reference at either side of the lsof read.
        All non-null peers must also be independently observed here. The
        original process owner must supply its retained endpoints, and retain
        parent ends until ended-child checks finish. These are sequential
        checkpoint observations, not atomic or continuous surveillance.
        """
        expected = exact_pipe_holders(endpoints, endpoints)
        if (not expected or set(births) != {row['pid'] for row in expected}
                or any(set(row) != {'pid', 'fd', 'kind', 'kernel_id', 'peer_kernel_id', 'access', 'path'}
                       or row['path'] is not None or row['access'] not in ('read', 'write') for row in expected)):
            raise ValueError('lcer.process_observation_invalid')
        by_handle = {row['kernel_id']: row for row in expected}
        if len(by_handle) != len(expected):
            raise ValueError('lcer.proof_pipe_extra_holder')
        for row in expected:
            peer = row['peer_kernel_id']
            if peer is not None and (peer not in by_handle or by_handle[peer]['peer_kernel_id'] != row['kernel_id']
                                     or by_handle[peer]['access'] == row['access']):
                raise ValueError('lcer.original_pipe_identity_mismatch')
        deadline = time.monotonic() + 60
        observations = []
        self.last_pipe_exclusivity = observations

        def observe(row):
            if time.monotonic() >= deadline:
                raise ValueError('lcer.pipe_holder_census_timeout')
            self._owned(row['pid'], births[row['pid']])
            actual, status = self._pipe_metadata(row['pid'], row['fd'])
            observations.append({'descriptor': actual, 'fi_status': status})
            if status & 1:  # PROC_FP_SHARED from sys/proc_info.h
                raise ValueError('lcer.proof_pipe_extra_holder')
            if row['peer_kernel_id'] is None and actual['peer_kernel_id'] is not None:
                raise ValueError('lcer.proof_pipe_extra_holder')
            if actual != row:
                raise ValueError('lcer.original_pipe_identity_mismatch')
            self._owned(row['pid'], births[row['pid']])
            return actual

        first = [observe(row) for row in expected]
        for pid in sorted(births):
            self._owned(pid, births[pid])
            selected = [row for row in first if row['pid'] == pid]
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError('lcer.pipe_holder_census_timeout')
            result = subprocess.run(['/usr/sbin/lsof', '-nP', '-a', '-p', str(pid), '-d',
                                     ','.join(str(row['fd']) for row in selected), '-F0pftand'],
                                    stdin=subprocess.DEVNULL, capture_output=True, close_fds=True,
                                    timeout=remaining)
            if result.returncode != 0 or result.stderr:
                raise ValueError('lcer.pipe_holder_census_unavailable')
            external = parse_lsof_descriptors(result.stdout, pid)
            if [row['fd'] for row in external] != [row['fd'] for row in selected]:
                raise ValueError('lcer.process_descriptors_changed')
            for row, independent in zip(selected, external):
                peer = row['peer_kernel_id']
                if (independent.get('type') != 'PIPE'
                        or independent.get('device') != '0x' + row['kernel_id'].lstrip('0')
                        or independent.get('name') != ('->0x' + peer.lstrip('0') if peer else '')
                        or independent.get('access') not in (' ', {'read': 'r', 'write': 'w'}[row['access']])):
                    raise ValueError('lcer.process_observation_invalid')
            self._owned(pid, births[pid])
        return exact_pipe_holders(first, [observe(row) for row in expected])

    def descriptors(self, pid, expected_birth):
        inventory = self.descriptor_list(pid, expected_birth)
        rows = []
        for fd, kind in inventory:
            if kind == 6:
                rows.append(self.pipe(pid, expected_birth, fd))
                continue
            if kind == 1:
                value = _VnodeDescriptor()
                if self._proc.proc_pidfdinfo(pid, fd, 2, ctypes.byref(value), ctypes.sizeof(value)) != ctypes.sizeof(value):
                    raise ValueError("lcer.process_observation_invalid")
                flags = value.file.flags
                path = os.fsdecode(bytes(value.vnode.path))
                if not path.startswith("/"):
                    raise ValueError("lcer.process_observation_invalid")
                inode = value.vnode.info.stat
                kernel_id = "%x:%x" % (inode.dev, inode.ino)
                label = "vnode"
            elif kind in (2, 3, 4, 5):
                # The public socket/pshm/psem/kqueue structs all begin with
                # proc_fileinfo followed by vinfo_stat. Only sockets expose
                # a further opaque kernel handle (socket_info.soi_so).
                flavor = {2: 3, 3: 5, 4: 4, 5: 7}[kind]
                raw = ctypes.create_string_buffer(16384)
                count = self._proc.proc_pidfdinfo(pid, fd, flavor, raw, len(raw))
                if count < ctypes.sizeof(_FileInfo) + ctypes.sizeof(_VnodeStat) or count >= len(raw):
                    raise ValueError("lcer.process_observation_invalid")
                flags = _FileInfo.from_buffer_copy(raw).flags
                inode = _VnodeStat.from_buffer_copy(raw, ctypes.sizeof(_FileInfo))
                kernel_id = "%x:%x" % (inode.dev, inode.ino)
                if kind == 2:
                    offset = ctypes.sizeof(_FileInfo) + ctypes.sizeof(_VnodeStat)
                    if count < offset + 8:
                        raise ValueError("lcer.process_observation_invalid")
                    kernel_id = "%016x" % struct.unpack_from("=Q", raw, offset)[0]
                label = {2: "socket", 3: "other", 4: "other", 5: "kqueue"}[kind]
                path = None
            else:
                # A new descriptor kind needs its actual kernel observation
                # contract before it can appear in a successful acquisition.
                raise ValueError("lcer.descriptor_kind_unclassified")
            access = {1: "read", 2: "write", 3: "read_write"}.get(flags & 3)
            if access is None:
                raise ValueError("lcer.process_observation_invalid")
            rows.append({"pid": pid, "fd": fd, "kind": label, "kernel_id": kernel_id,
                         "peer_kernel_id": None, "access": access, "path": path})
        if inventory != self.descriptor_list(pid, expected_birth):
            raise ValueError("lcer.process_descriptors_changed")
        return rows

    def lsof_descriptors(self, pid, expected_birth):
        self._owned(pid, expected_birth)
        result = subprocess.run(["/usr/sbin/lsof", "-nP", "-a", "-p", str(pid), "-d", "0-2147483647", "-F0pftand"],
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=60, close_fds=True)
        if result.returncode != 0 or result.stderr:
            raise ValueError("lcer.process_observation_invalid")
        rows = parse_lsof_descriptors(result.stdout, pid)
        self._owned(pid, expected_birth)
        return rows

    def checked_descriptors(self, pid, expected_birth):
        descriptors = self.descriptors(pid, expected_birth)
        external = self.lsof_descriptors(pid, expected_birth)
        if [row["fd"] for row in descriptors] != [row["fd"] for row in external]:
            raise ValueError("lcer.process_descriptors_changed")
        for kernel, lsof in zip(descriptors, external):
            # Darwin lsof leaves access blank for pipes. Access then comes
            # from the separately acquired proc_fileinfo.fi_openflags.
            if lsof.get("access") not in (" ", {"read": "r", "write": "w", "read_write": "u"}[kernel["access"]]):
                raise ValueError("lcer.process_observation_invalid")
            if kernel["kind"] == "pipe":
                expected = "->0x" + kernel["peer_kernel_id"].lstrip("0") if kernel["peer_kernel_id"] is not None else ""
                if (lsof.get("type") != "PIPE" or lsof.get("name") != expected or
                        lsof.get("device") != "0x" + kernel["kernel_id"].lstrip("0")):
                    raise ValueError("lcer.process_observation_invalid")
            elif kernel["kind"] == "vnode":
                if lsof.get("name") != kernel["path"]:
                    raise ValueError("lcer.process_observation_invalid")
            elif kernel["kind"] == "kqueue" and lsof.get("type") != "KQUEUE":
                raise ValueError("lcer.process_observation_invalid")
        if descriptors != self.descriptors(pid, expected_birth):
            raise ValueError("lcer.process_descriptors_changed")
        return descriptors

    def image_mappings(self, pid, expected_birth):
        identity = self._owned(pid, expected_birth)
        paths = self.paths(pid, expected_birth)
        result = subprocess.run(['/usr/bin/vmmap', '-w', str(pid)], stdin=subprocess.DEVNULL,
                                capture_output=True, close_fds=True, timeout=60)
        if result.returncode != 0 or result.stderr:
            raise ValueError('lcer.process_images_unavailable')
        rows = vmmap_image_paths(result.stdout, pid, identity['ppid'], paths['executable_realpath'])
        if self.paths(pid, expected_birth) != paths:
            raise ValueError('lcer.process_identity_mismatch')
        return rows

    def pipe_holder_census(self, endpoints):
        """Retain visible pipe holders and every gap in kernel visibility.

        This diagnostic cannot grant acquisition acceptance. In particular,
        EPERM is an unobserved process, never evidence that its pipes differ.
        """
        handles = {row['kernel_id'] for row in endpoints}
        if not handles or any(re.fullmatch('[0-9a-f]{16}', value) is None for value in handles):
            raise ValueError('lcer.process_observation_invalid')
        deadline = time.monotonic() + 60
        count = self._proc.proc_listpids(1, 0, None, 0)
        if count <= 0 or count % 4 or count > 4 * 1024 * 1024:
            raise ValueError('lcer.pipe_holder_census_unavailable')
        buffer = (ctypes.c_int * (count // 4 + 256))()
        actual = self._proc.proc_listpids(1, 0, buffer, ctypes.sizeof(buffer))
        if actual <= 0 or actual >= ctypes.sizeof(buffer) or actual % 4:
            raise ValueError('lcer.pipe_holder_census_unavailable')
        pids = sorted(set(buffer[:actual // 4]) - {0})
        if any(pid < 0 for pid in pids):
            raise ValueError('lcer.process_observation_invalid')
        unavailable, exited, holders = [], [], []
        for pid in pids:
            if time.monotonic() >= deadline:
                raise ValueError('lcer.pipe_holder_census_timeout')
            ctypes.set_errno(0)
            size = self._proc.proc_pidinfo(pid, 1, 0, None, 0)
            error = ctypes.get_errno()
            if size <= 0:
                if error == errno.ESRCH:
                    exited.append(pid)
                else:
                    unavailable.append({'pid': pid, 'operation': 'PROC_PIDLISTFDS', 'errno': error})
                continue
            if size % ctypes.sizeof(_DescriptorInfo) or size > 64 * 1024 * 1024:
                raise ValueError('lcer.process_observation_invalid')
            entries = (_DescriptorInfo * (size // ctypes.sizeof(_DescriptorInfo) + 32))()
            ctypes.set_errno(0)
            used = self._proc.proc_pidinfo(pid, 1, 0, entries, ctypes.sizeof(entries))
            error = ctypes.get_errno()
            if used <= 0:
                if error == errno.ESRCH:
                    exited.append(pid)
                else:
                    unavailable.append({'pid': pid, 'operation': 'PROC_PIDLISTFDS', 'errno': error})
                continue
            if used >= ctypes.sizeof(entries) or used % ctypes.sizeof(_DescriptorInfo):
                raise ValueError('lcer.process_descriptors_changed')
            descriptors = entries[:used // ctypes.sizeof(_DescriptorInfo)]
            if len({row.fd for row in descriptors}) != len(descriptors) or any(row.fd < 0 for row in descriptors):
                raise ValueError('lcer.process_observation_invalid')
            matches = []
            for entry in descriptors:
                if entry.kind != 6:
                    continue
                pipe = _PipeInfo()
                ctypes.set_errno(0)
                observed = self._proc.proc_pidfdinfo(pid, entry.fd, 6, ctypes.byref(pipe), ctypes.sizeof(pipe))
                error = ctypes.get_errno()
                if observed != ctypes.sizeof(pipe):
                    # An fd can close while the census runs. Record the gap;
                    # do not silently treat inaccessible metadata as absent.
                    unavailable.append({'pid': pid, 'fd': entry.fd, 'operation': 'PROC_PIDFDPIPEINFO', 'errno': error})
                    continue
                if '%016x' % pipe.handle in handles:
                    matches.append(self._pipe_record(pid, entry.fd))
            if not matches:
                continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError('lcer.pipe_holder_census_timeout')
            # Only known matching numeric descriptors. This avoids lsof's
            # blocking filesystem work across every descriptor on the host.
            result = subprocess.run(['/usr/sbin/lsof', '-nP', '-a', '-p', str(pid),
                                     '-d', ','.join(str(row['fd']) for row in matches), '-F0pftnd'],
                                    stdin=subprocess.DEVNULL, capture_output=True,
                                    timeout=remaining, close_fds=True)
            if result.returncode != 0 or result.stderr:
                raise ValueError('lcer.pipe_holder_census_unavailable')
            rows = parse_lsof_descriptors(result.stdout, pid)
            if [row['fd'] for row in rows] != sorted(row['fd'] for row in matches):
                raise ValueError('lcer.process_descriptors_changed')
            for expected, row in zip(sorted(matches, key=lambda item: item['fd']), rows):
                observed = self._pipe_record(pid, row['fd'])
                if (observed != expected or row.get('type') != 'PIPE' or
                        row.get('device') != '0x' + observed['kernel_id'].lstrip('0') or
                        row.get('name') != ('->0x' + observed['peer_kernel_id'].lstrip('0') if observed['peer_kernel_id'] is not None else '')):
                    raise ValueError('lcer.process_descriptors_changed')
                holders.append(observed)
        census = {'enumerated_pids': pids, 'exited_pids': exited, 'unavailable': unavailable,
                  'holders': sorted(holders, key=lambda row: (row['pid'], row['fd']))}
        self.last_pipe_census = census
        return census

    def pipe_holders(self, endpoints):
        census = self.pipe_holder_census(endpoints)
        if census['unavailable']:
            raise ValueError('lcer.pipe_holder_census_unavailable')
        return census['holders']


class OriginalPipeProcess:
    """One suspended exec with three original pipes and a retained wait handle.

    The acquisition owner keeps this object through stream drainage. There is
    no restart path and no process-group or service-wide signal operation.
    """

    def __init__(self, observer):
        self.observer = observer
        self.pid = None
        self.birth = None
        self.returncode = None
        self.stdin_fd = None
        self.stdout_fd = None
        self.stderr_fd = None
        self.exec_descriptors = None
        self.parent_descriptors = None
        self._resumed = False
        self._wait_lock = threading.Lock()
        self.launch_validation = None
        self._launch_inputs_raw = None

    def start(self, argv, environment, cwd):
        if self.pid is not None or not argv or not all(type(arg) is str and arg and '\0' not in arg for arg in argv):
            raise ValueError("lcer.operation_sequence_invalid")
        if (not Path(argv[0]).is_absolute() or not Path(cwd).is_absolute() or Path(cwd).resolve() != Path(cwd)
                or not all(type(k) is str and k and '=' not in k and '\0' not in k and
                           type(v) is str and '\0' not in v for k, v in environment.items())):
            raise ValueError("lcer.process_input_invalid")
        self._launch_inputs_raw = stored_json_bytes({
            'argv': list(argv), 'environment': dict(environment), 'cwd_realpath': str(cwd),
            'executable_realpath': str(Path(argv[0]).resolve())})
        libc = self.observer._libc
        action_pointer = ctypes.POINTER(ctypes.c_void_p)
        libc.posix_spawn_file_actions_init.argtypes = [action_pointer]
        libc.posix_spawn_file_actions_destroy.argtypes = [action_pointer]
        libc.posix_spawn_file_actions_adddup2.argtypes = [action_pointer, ctypes.c_int, ctypes.c_int]
        libc.posix_spawn_file_actions_addclose.argtypes = [action_pointer, ctypes.c_int]
        libc.posix_spawn_file_actions_addchdir_np.argtypes = [action_pointer, ctypes.c_char_p]
        libc.posix_spawnattr_init.argtypes = [action_pointer]
        libc.posix_spawnattr_destroy.argtypes = [action_pointer]
        libc.posix_spawnattr_setflags.argtypes = [action_pointer, ctypes.c_short]
        libc.posix_spawn.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_char_p, action_pointer, action_pointer,
                                    ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p)]
        libc.posix_spawn.restype = ctypes.c_int
        actions = ctypes.c_void_p()
        attributes = ctypes.c_void_p()
        pipes = []
        try:
            if libc.posix_spawn_file_actions_init(ctypes.byref(actions)) != 0:
                raise ValueError("lcer.process_spawn_failed")
            if libc.posix_spawnattr_init(ctypes.byref(attributes)) != 0:
                raise ValueError("lcer.process_spawn_failed")
            for _ in range(3):
                pipes.extend(os.pipe())
            if any(fd < 3 for fd in pipes):
                raise ValueError("lcer.parent_standard_descriptors_missing")
            for fd in pipes:
                os.set_inheritable(fd, False)
            for source, target in [(pipes[0], 0), (pipes[3], 1), (pipes[5], 2)]:
                if libc.posix_spawn_file_actions_adddup2(ctypes.byref(actions), source, target) != 0:
                    raise ValueError("lcer.process_spawn_failed")
            for fd in pipes:
                if libc.posix_spawn_file_actions_addclose(ctypes.byref(actions), fd) != 0:
                    raise ValueError("lcer.process_spawn_failed")
            if libc.posix_spawn_file_actions_addchdir_np(ctypes.byref(actions), os.fsencode(cwd)) != 0:
                raise ValueError("lcer.process_spawn_failed")
            # START_SUSPENDED | SETSID | CLOEXEC_DEFAULT. Read the child's
            # actual descriptor table before any dyld or engine execution.
            if libc.posix_spawnattr_setflags(ctypes.byref(attributes), 0x0080 | 0x0400 | 0x4000) != 0:
                raise ValueError("lcer.process_spawn_failed")
            arguments = (ctypes.c_char_p * (len(argv) + 1))(*[arg.encode('utf-8') for arg in argv], None)
            values = [('%s=%s' % (key, environment[key])).encode('utf-8') for key in sorted(environment)]
            envp = (ctypes.c_char_p * (len(values) + 1))(*values, None)
            pid = ctypes.c_int()
            result = libc.posix_spawn(ctypes.byref(pid), arguments[0], ctypes.byref(actions), ctypes.byref(attributes), arguments, envp)
            if result != 0:
                raise OSError(result, os.strerror(result))
            self.pid = pid.value
            self.stdin_fd, self.stdout_fd, self.stderr_fd = pipes[1], pipes[2], pipes[4]
        finally:
            if actions.value:
                libc.posix_spawn_file_actions_destroy(ctypes.byref(actions))
            if attributes.value:
                libc.posix_spawnattr_destroy(ctypes.byref(attributes))
            for fd in pipes:
                if fd not in (self.stdin_fd, self.stdout_fd, self.stderr_fd):
                    os.close(fd)
        # The owning object retains PID and original pipes even if validation
        # fails. Its caller must retain and clean it as an acquisition failure.
        identity = self.observer.identity(self.pid)
        self.birth = identity['macos_birth_tuple']
        if identity['ppid'] != os.getpid():
            raise ValueError("lcer.process_identity_mismatch")
        if self.observer.descriptor_list(self.pid, self.birth) != [(0, 6), (1, 6), (2, 6)]:
            raise ValueError("lcer.inherited_descriptor_invalid")
        self.exec_descriptors = [self.observer.pipe(self.pid, self.birth, fd) for fd in range(3)]
        parent_birth = self.observer.identity(os.getpid())['macos_birth_tuple']
        self.parent_descriptors = [self.observer.pipe(os.getpid(), parent_birth, fd)
                                   for fd in (self.stdin_fd, self.stdout_fd, self.stderr_fd)]
        for child, parent in zip(self.exec_descriptors, self.parent_descriptors):
            if (child['kernel_id'] != parent['peer_kernel_id'] or child['peer_kernel_id'] != parent['kernel_id'] or
                    child['access'] != ('read' if child['fd'] == 0 else 'write') or
                    parent['access'] != ('write' if child['fd'] == 0 else 'read')):
                raise ValueError("lcer.original_pipe_identity_mismatch")
        observed_paths = self.observer.paths(self.pid, self.birth)
        observed_argv, observed_environment = self.observer.launch_inputs(self.pid, self.birth)
        self.launch_validation = {
            'pid': self.pid, 'birth': self.birth, 'observed_paths': observed_paths,
            'expected_paths': {'cwd_realpath': str(cwd), 'executable_realpath': str(Path(argv[0]).resolve())},
            'argv_matches': observed_argv == argv,
            'missing_environment_keys': sorted(set(environment) - set(observed_environment)),
            'extra_environment_keys': sorted(set(observed_environment) - set(environment)),
            'changed_environment_keys': sorted(key for key in environment if key in observed_environment and
                                               environment[key] != observed_environment[key])}
        if (observed_paths != self.launch_validation['expected_paths'] or
                observed_argv != argv or observed_environment != environment):
            raise ValueError("lcer.process_input_invalid")
        return self

    def poll(self):
        with self._wait_lock:
            return self._poll_unlocked()

    def _poll_unlocked(self):
        if self.pid is None:
            raise ValueError("lcer.operation_sequence_invalid")
        if self.returncode is None:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                if os.WIFEXITED(status):
                    self.returncode = os.WEXITSTATUS(status)
                elif os.WIFSIGNALED(status):
                    self.returncode = -os.WTERMSIG(status)
                else:
                    raise ValueError("lcer.process_wait_invalid")
        return self.returncode

    def send_signal(self, value):
        if value not in (signal.SIGCONT, signal.SIGTERM, signal.SIGKILL):
            raise ValueError("lcer.process_signal_invalid")
        with self._wait_lock:
            # Keep the child unreaped from identity check through signal.
            # Another observer thread cannot release its PID in this interval.
            if self._poll_unlocked() is not None:
                return False
            self.observer._owned(self.pid, self.birth)
            os.kill(self.pid, value)
            return True

    def resume(self):
        if self._resumed or self.exec_descriptors is None:
            raise ValueError("lcer.operation_sequence_invalid")
        if not self.send_signal(signal.SIGCONT):
            raise ValueError("lcer.original_process_exited")
        self._resumed = True

    def wait(self, timeout):
        deadline = time.monotonic() + timeout
        while self.poll() is None:
            if time.monotonic() >= deadline:
                raise TimeoutError("lcer.process_exit_timeout")
            time.sleep(0.01)
        return self.returncode

    def observe_original_holders(self):
        """Sample this launch's retained three pipes before they are closed.

        A reaped original contributes no current child fd rows. Each parent
        end must remain unique and have a null peer. A helper retaining either
        side therefore rejects even after the original has exited.
        """
        if self.exec_descriptors is None or self.parent_descriptors is None:
            raise ValueError('lcer.operation_sequence_invalid')
        retained = (self.stdin_fd, self.stdout_fd, self.stderr_fd)
        if retained != tuple(row['fd'] for row in self.parent_descriptors):
            raise ValueError('lcer.original_pipe_identity_mismatch')
        with self._wait_lock:
            returncode = self._poll_unlocked()
            parent_birth = self.observer.identity(os.getpid())['macos_birth_tuple']
            births = {os.getpid(): parent_birth}
            if returncode is None:
                self.observer._owned(self.pid, self.birth)
                endpoints = [dict(row) for row in self.parent_descriptors + self.exec_descriptors]
                births[self.pid] = self.birth
            else:
                endpoints = [{**row, 'peer_kernel_id': None} for row in self.parent_descriptors]
            holders = self.observer.exclusive_pipe_holders(endpoints, births)
            if self._poll_unlocked() != returncode:
                raise ValueError('lcer.process_state_changed')
            return {'poll_returncode': returncode,
                    'pipe_endpoints': sorted(endpoints, key=lambda row: (row['pid'], row['fd'])),
                    'pipe_holders': holders}

    def close_pipes(self):
        # Read each owned descriptor once. A failed close leaves that field
        # and all later descriptors unchanged; successful closes clear it.
        fd = self.stdin_fd
        if fd is not None:
            os.close(fd)
            self.stdin_fd = None
        fd = self.stdout_fd
        if fd is not None:
            os.close(fd)
            self.stdout_fd = None
        fd = self.stderr_fd
        if fd is not None:
            os.close(fd)
            self.stderr_fd = None


class CaptureBudget:
    """One caller-supplied disk budget shared by every original stream."""

    def __init__(self, limit_bytes):
        if type(limit_bytes) is not int or limit_bytes <= 0:
            raise ValueError('lcer.capture_budget_invalid')
        self.limit_bytes = limit_bytes
        self.used_bytes = 0
        self._lock = threading.Lock()

    def claim(self, count):
        with self._lock:
            if type(count) is not int or count < 0 or count > self.limit_bytes - self.used_bytes:
                raise ValueError('lcer.capture_budget_exhausted')
            self.used_bytes += count


class OriginalPipeMonitor:
    """Continuously retain both original output pipes while the parent works.

    The thread records transport only. It cannot issue commands, choose Q,
    classify worlds, mutate canonical state, signal, restart or accept proof.
    """

    def __init__(self, process, stdout_path, stderr_path, budget):
        if process.pid is None or process._resumed or process.exec_descriptors is None:
            raise ValueError('lcer.operation_sequence_invalid')
        self.process = process
        self.budget = budget
        self._condition = threading.Condition()
        self._lines = deque()
        self._failure = None
        self._eof = set()
        self._positions = {'stdout': 0, 'stderr': 0}
        self._pending_stdout = bytearray()
        self._line_offset = 0
        self._stdin = bytearray()
        self._stdin_lock = threading.Lock()
        self._files = {}
        self._fds = {'stdout': process.stdout_fd, 'stderr': process.stderr_fd}
        self._started = False
        self._finished = False
        paths = [Path(stdout_path), Path(stderr_path)]
        if paths[0] == paths[1] or any(not path.is_absolute() or path.parent.resolve() != path.parent or path.exists() or path.is_symlink() for path in paths):
            raise ValueError('lcer.capture_path_invalid')
        try:
            for name, path in zip(('stdout', 'stderr'), paths):
                self._files[name] = path.open('xb', buffering=0)
                os.set_blocking(self._fds[name], False)
            os.set_blocking(process.stdin_fd, False)
        except BaseException:
            for stream in self._files.values():
                stream.close()
            raise
        self._thread = threading.Thread(target=self._drain, name='city-original-pipe-reader', daemon=True)

    def start(self):
        if self._started or self._finished:
            raise ValueError('lcer.operation_sequence_invalid')
        self._started = True
        self._thread.start()

    def _drain(self):
        active = {fd: name for name, fd in self._fds.items()}
        try:
            while active:
                ready, _, _ = select.select(list(active), [], [], 0.01)
                for fd in ready:
                    name = active[fd]
                    try:
                        raw = os.read(fd, 65536)
                    except BlockingIOError:
                        continue
                    if not raw:
                        del active[fd]
                        with self._condition:
                            self._eof.add(name)
                            if name == 'stdout' and self._pending_stdout:
                                # A partial final log line is retained. A partial
                                # protocol line is an acquisition failure.
                                if self._pending_stdout.lstrip().startswith(b'{'):
                                    self._failure = ValueError('lcer.protocol_line_truncated')
                                self._pending_stdout.clear()
                            self._condition.notify_all()
                        continue
                    self.budget.claim(len(raw))
                    stream = self._files[name]
                    view = memoryview(raw)
                    while view:
                        written = stream.write(view)
                        if written is None or written <= 0:
                            raise OSError('lcer.capture_write_failed')
                        view = view[written:]
                    with self._condition:
                        self._positions[name] += len(raw)
                        if name == 'stdout':
                            self._pending_stdout.extend(raw)
                            while True:
                                end = self._pending_stdout.find(b'\n')
                                if end < 0:
                                    break
                                line = bytes(self._pending_stdout[:end + 1])
                                del self._pending_stdout[:end + 1]
                                if line.lstrip().startswith(b'{'):
                                    self._lines.append((self._line_offset, line))
                                self._line_offset += len(line)
                        self._condition.notify_all()
        except BaseException as error:
            with self._condition:
                self._failure = error
                self._condition.notify_all()
        finally:
            for stream in self._files.values():
                stream.close()
            with self._condition:
                self._finished = True
                self._condition.notify_all()

    def observation(self):
        with self._condition:
            state = {'stream_sizes': dict(self._positions), 'eof': sorted(self._eof),
                     'finished': self._finished, 'failure': str(self._failure) if self._failure else None}
        state['poll_returncode'] = self.process.poll()
        return state

    def next_protocol_line(self, timeout):
        if not self._started or type(timeout) not in (int, float) or not 0 < timeout <= 60:
            raise ValueError('lcer.operation_sequence_invalid')
        deadline = time.monotonic() + timeout
        with self._condition:
            while True:
                if self._failure is not None:
                    raise self._failure
                if self._lines:
                    offset, raw = self._lines.popleft()
                    return offset, raw
                if 'stdout' in self._eof:
                    raise EOFError('lcer.original_stdout_eof')
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('lcer.operation_timeout')
                self._condition.wait(min(remaining, 0.05))

    def send(self, raw, timeout=60):
        if not self._started or self.process.stdin_fd is None or type(timeout) not in (int, float) or not 0 < timeout <= 60:
            raise ValueError('lcer.operation_sequence_invalid')
        parse_stored_json(raw)
        deadline = time.monotonic() + timeout
        with self._stdin_lock:
            offset = len(self._stdin)
            remaining = memoryview(raw)
            while remaining:
                if self.process.poll() is not None:
                    raise ValueError('lcer.original_process_exited')
                with self._condition:
                    if self._failure is not None:
                        raise self._failure
                wait = deadline - time.monotonic()
                if wait <= 0:
                    raise TimeoutError('lcer.operation_timeout')
                _, ready, _ = select.select([], [self.process.stdin_fd], [], min(wait, 0.05))
                if not ready:
                    continue
                try:
                    written = os.write(self.process.stdin_fd, remaining)
                except BlockingIOError:
                    continue
                if written <= 0:
                    raise OSError('lcer.command_write_failed')
                self._stdin.extend(remaining[:written])
                remaining = remaining[written:]
            return offset

    def stdin_bytes(self):
        with self._stdin_lock:
            return bytes(self._stdin)

    def finish(self, timeout=60):
        if not self._started or type(timeout) not in (int, float) or not 0 < timeout <= 60:
            raise ValueError('lcer.operation_sequence_invalid')
        self._thread.join(timeout)
        if self._thread.is_alive():
            raise TimeoutError('lcer.pipe_drain_timeout')
        if self._failure is not None:
            raise self._failure
        if self._eof != {'stdout', 'stderr'}:
            raise ValueError('lcer.original_pipe_drain_incomplete')
        return self.observation()


class RawTraceWriter:
    """Append validated events with hashes of the actual preceding stored line."""

    def __init__(self, contract_raw, path):
        self.validator = FrozenWireValidator(contract_raw)
        path = Path(path)
        if not path.is_absolute() or path.parent.resolve() != path.parent or path.is_symlink():
            raise ValueError('lcer.capture_path_invalid')
        self.stream = path.open('xb')
        self._rows = []
        self._previous = None

    def append(self, event_id, payload, domain=None, operation_id=None):
        self.validator.validate(event_id, payload)
        nested = payload
        if event_id == 'wire_event':
            nested = parse_stored_json(payload['raw_line_utf8'].encode('utf-8'))
            self.validator.validate(payload['parsed_schema'], nested)
            if (payload['direction'] == 'stdin') != (payload['parsed_schema'] == 'command'):
                raise ValueError('lcer.trace_relation_invalid')
        if (('domain' in nested and nested['domain'] != domain) or
                ('operation_id' in nested and nested['operation_id'] != operation_id)):
            raise ValueError('lcer.trace_relation_invalid')
        row = {'sequence': len(self._rows), 'event_id': event_id, 'operation_id': operation_id,
               'domain': domain, 'monotonic_ns': time.monotonic_ns(), 'payload': payload,
               'previous_event_sha256': self._previous}
        self.validator.validate('trace_event', row)
        raw = stored_json_bytes(row)
        if self.stream.write(raw) != len(raw):
            raise OSError('lcer.trace_write_failed')
        self.stream.flush()
        self._rows.append(raw)
        self._previous = hashlib.sha256(raw).hexdigest()
        return parse_stored_json(raw)

    def rows(self):
        return [parse_stored_json(raw) for raw in self._rows]

    def close(self):
        self.stream.close()


class OriginalProtocolConnection:
    """One startup and one original bound command stream; no retry route.

    This enforces wire relations only. The acquisition owner must independently
    authenticate process/world inputs before binding and before accepting any
    returned physical evidence or canonical consequence.
    """

    def __init__(self, contract_raw, witness_id, domain, launch_id, monitor, trace):
        self.validator = FrozenWireValidator(contract_raw)
        self.policy = FrozenObligationPlanCompiler(contract_raw).compile()['constitutional_policy']
        if domain not in ('domain_A', 'domain_B') or not witness_id or not launch_id:
            raise ValueError('lcer.process_input_invalid')
        self.witness_id, self.domain, self.launch_id = witness_id, domain, launch_id
        self.monitor, self.trace = monitor, trace
        self.startup_raw = None
        self.binding_sha256 = None
        self._operations = set()
        self._failed = False
        self._shutdown = False

    def _read(self, deadline, operation_id):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('lcer.operation_timeout')
        offset, raw = self.monitor.next_protocol_line(min(remaining, 60))
        message = parse_stored_json(raw)
        matches = []
        for kind in ('startup', 'response', 'physical_event', 'fault_event'):
            try:
                self.validator.validate(kind, message)
                matches.append(kind)
            except ValueError:
                pass
        if len(matches) != 1:
            raise ValueError('lcer.schema_invalid')
        kind = matches[0]
        if kind == 'fault_event':
            if message['failure_case'] != self.witness_id or message['executor'] != 'unreal' or operation_id is None:
                raise ValueError('lcer.protocol_identity_mismatch')
        else:
            if any(message[key] != value for key, value in (
                    ('witness_id', self.witness_id), ('domain', self.domain), ('launch_id', self.launch_id))):
                raise ValueError('lcer.protocol_identity_mismatch')
            if message.get('operation_id') != operation_id:
                raise ValueError('lcer.protocol_operation_mismatch')
        self.trace.append('wire_event', {'direction': 'stdout', 'raw_line_utf8': raw.decode('utf-8'),
                                        'stream_byte_offset': offset, 'parsed_schema': kind},
                          self.domain, operation_id)
        return kind, message, raw

    def read_startup(self, timeout=60):
        if self.startup_raw is not None or self._failed or type(timeout) not in (int, float) or not 0 < timeout <= 60:
            raise ValueError('lcer.operation_sequence_invalid')
        try:
            kind, message, raw = self._read(time.monotonic() + timeout, None)
            if kind != 'startup':
                raise ValueError('lcer.protocol_startup_missing')
            self.startup_raw = raw
            return parse_stored_json(raw)
        except BaseException:
            self._failed = True
            raise

    def bind(self, binding, timeout=60):
        if self.binding_sha256 is not None or self.startup_raw is None:
            raise ValueError('lcer.operation_sequence_invalid')
        self.validator.validate('process_binding', binding)
        startup = parse_stored_json(self.startup_raw)
        if (any(binding[key] != startup[key] for key in ('witness_id', 'domain', 'launch_id', 'pid')) or
                binding['startup_sha256'] != hashlib.sha256(self.startup_raw).hexdigest()):
            raise ValueError('lcer.process_identity_mismatch')
        value = hashlib.sha256(stored_json_bytes(binding)).hexdigest()
        result = self._exchange('bind', 'bind_0001', binding, value, timeout)
        if result['response']['status'] == 'ok':
            if result['response']['payload']['startup_sha256'] != binding['startup_sha256']:
                self._failed = True
                raise ValueError('lcer.protocol_identity_mismatch')
            self.binding_sha256 = value
        else:
            self._failed = True
        return result

    def request(self, command, operation_id, payload=None, timeout=60):
        if command == 'bind' or self.binding_sha256 is None:
            raise ValueError('lcer.operation_sequence_invalid')
        return self._exchange(command, operation_id, payload, self.binding_sha256, timeout)

    def _exchange(self, command, operation_id, payload, binding_sha256, timeout):
        allowed = {'bind': {'bind_0001'}, 'materialize': {'materialize_0001', 'materialize_0002'},
                   'emit': {'emit_0001'}, 'inspect': {'inspect_terminal', *('inspect_L%d' % i for i in range(6))},
                   'arm_fault': {'arm_fault_0001'}, 'shutdown': {'shutdown_0001'}}
        if (self._failed or self._shutdown or self.startup_raw is None or operation_id in self._operations or
                operation_id not in allowed.get(command, set()) or
                type(timeout) not in (int, float) or not 0 < timeout <= 60):
            raise ValueError('lcer.operation_sequence_invalid')
        argument_schema = {'bind': 'process_binding', 'materialize': 'materialize_input', 'arm_fault': 'fault_arm'}.get(command)
        if argument_schema is not None:
            self.validator.validate(argument_schema, payload)
        elif payload is not None:
            raise ValueError('lcer.schema_invalid')
        if command == 'bind':
            startup = parse_stored_json(self.startup_raw)
            if (self.binding_sha256 is not None or binding_sha256 != hashlib.sha256(stored_json_bytes(payload)).hexdigest()
                    or any(payload[key] != startup[key] for key in ('witness_id', 'domain', 'launch_id', 'pid'))
                    or payload['startup_sha256'] != hashlib.sha256(self.startup_raw).hexdigest()):
                raise ValueError('lcer.process_identity_mismatch')
        elif self.binding_sha256 is None or binding_sha256 != self.binding_sha256:
            raise ValueError('lcer.binding_mismatch')
        request = {'schema': 'city.live_evidence_command.v1', 'witness_id': self.witness_id,
                   'domain': self.domain, 'launch_id': self.launch_id, 'operation_id': operation_id,
                   'binding_sha256': binding_sha256, 'command': command, 'payload': payload}
        self.validator.validate('command', request)
        raw = stored_json_bytes(request)
        before_fault = None
        if self.witness_id == 'F18' and self.domain == 'domain_A' and operation_id == 'materialize_0002':
            required = {'bind_0001', 'materialize_0001', 'emit_0001', 'inspect_L0', 'inspect_L1', 'inspect_L2', 'inspect_L3'}
            expected_r1 = self.policy['canonical_records'][
                'proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R1.json']
            record_raw = payload['record_raw_utf8'].encode('utf-8')
            projection = {'schema': 'city.live_evidence_projection.v1', 'witness_id': self.witness_id,
                          'domain': self.domain, 'launch_id': self.launch_id, 'operation_id': operation_id,
                          'binding_sha256': self.binding_sha256, 'record_role': 'R1',
                          'record_raw_sha256': expected_r1, 'record_canonical_hash': hashlib.sha256(record_raw[:-1]).hexdigest(),
                          'generation': 1, 'allocation_owner': 'domain_A'}
            if (not required <= self._operations or payload['projection'] != projection
                    or hashlib.sha256(record_raw).hexdigest() != expected_r1
                    or payload['launch_receipt_raw_utf8'] is not None):
                raise ValueError('lcer.operation_sequence_invalid')
            before_fault = raw
            request['binding_sha256'] = '0' * 64
            raw = stored_json_bytes(request)
        deadline = time.monotonic() + timeout
        self._operations.add(operation_id)
        physical = None
        faults = []
        try:
            offset = self.monitor.send(raw, timeout)
            self.trace.append('wire_event', {'direction': 'stdin', 'raw_line_utf8': raw.decode('utf-8'),
                                            'stream_byte_offset': offset, 'parsed_schema': 'command'},
                              self.domain, operation_id)
            while True:
                kind, message, _ = self._read(deadline, operation_id)
                if kind == 'fault_event':
                    if faults:
                        raise ValueError('lcer.protocol_duplicate_event')
                    faults.append(message)
                    continue
                if kind == 'physical_event':
                    if command != 'emit' or physical is not None or message['binding_sha256'] != binding_sha256:
                        raise ValueError('lcer.protocol_event_mismatch')
                    physical = message
                    continue
                if kind != 'response':
                    raise ValueError('lcer.protocol_duplicate_startup')
                if any(message[key] != request[key] for key in (
                        'witness_id', 'domain', 'launch_id', 'operation_id', 'binding_sha256', 'command')):
                    raise ValueError('lcer.protocol_response_mismatch')
                if message['status'] == 'error':
                    if message['error'] is None or message['payload'] is not None:
                        raise ValueError('lcer.protocol_response_mismatch')
                else:
                    if message['error'] is not None or message['payload'] is None:
                        raise ValueError('lcer.protocol_response_mismatch')
                    self.validator.validate(self.policy['schema_contract']['response_match'][command], message['payload'])
                    if any(message['payload'][key] != request[key] for key in (
                            'witness_id', 'domain', 'launch_id', 'operation_id', 'binding_sha256') if key in message['payload']):
                        raise ValueError('lcer.protocol_response_mismatch')
                if command == 'emit':
                    if message['status'] == 'ok' and (physical is None or message['payload']['physical_event'] != physical):
                        raise ValueError('lcer.protocol_event_mismatch')
                    if message['status'] == 'error' and physical is not None:
                        raise ValueError('lcer.protocol_event_mismatch')
                if command == 'shutdown':
                    self._shutdown = True
                if before_fault is not None:
                    program = next(row for row in self.policy['failure_programs'] if row['id'] == 'F18')
                    fault = {'failure_case': 'F18', 'executor': 'harness', 'stage': program['stage'],
                             'action': program['action'], 'consumed': True,
                             'underlying_code': None if message['error'] is None else message['error']['underlying_code'],
                             'before': {'kind': 'bytes', 'semantic_type': 'materialize_command',
                                        'raw_base64': base64.b64encode(before_fault).decode('ascii')},
                             'after': {'kind': 'bytes', 'semantic_type': 'materialize_command',
                                       'raw_base64': base64.b64encode(raw).decode('ascii')}}
                    self.trace.append('fault_event', fault, self.domain, operation_id)
                    faults.append(fault)
                return {'response': message, 'physical_event': physical, 'fault_events': faults}
        except BaseException:
            self._failed = True
            raise


class OriginalProcessEvidence:
    """Join the original protocol stream to fresh parent process observations.

    This records process and pipe facts. The acquisition owner and independent
    verifier must still validate build inputs, startup worlds, bindings and the
    complete case. A matching process record grants no representation claim.
    """

    def __init__(self, contract_raw, connection, cache, runtime_inputs=None):
        self.validator = FrozenWireValidator(contract_raw)
        if runtime_inputs is not None and (not isinstance(runtime_inputs, RuntimeBuildInputInventory)
                                            or runtime_inputs.cache != cache):
            raise ValueError('lcer.runtime_input_inventory_invalid')
        self._runtime_inputs = runtime_inputs
        self.connection = connection
        self.process = connection.monitor.process
        self.observer = self.process.observer
        if (self.process.pid is None or self.process.birth is None or
                self.process.exec_descriptors is None or self.process._launch_inputs_raw is None):
            raise ValueError('lcer.operation_sequence_invalid')
        self._identity_raw = stored_json_bytes({'pid': self.process.pid, 'birth': self.process.birth})
        self._launch_raw = self.process._launch_inputs_raw
        self._routing = (connection.witness_id, connection.domain, connection.launch_id)
        self._cache_raw = stored_json_bytes(cache)
        self._startup_raw = None
        self._checkpoints = set()
        self._failed = False

    def _verify_original(self):
        if (self.connection.monitor.process is not self.process or self.process.observer is not self.observer or
                stored_json_bytes({'pid': self.process.pid, 'birth': self.process.birth}) != self._identity_raw or
                self.process._launch_inputs_raw != self._launch_raw or
                (self.connection.witness_id, self.connection.domain, self.connection.launch_id) != self._routing):
            raise ValueError('lcer.original_process_identity_mismatch')

    def _observe_process(self):
        startup_raw = self.connection.startup_raw
        if startup_raw is None:
            raise ValueError('lcer.protocol_startup_missing')
        startup = self.validator.parse('startup', startup_raw)
        if (self._startup_raw is not None and startup_raw != self._startup_raw) or (
                (startup['witness_id'], startup['domain'], startup['launch_id']) != self._routing):
            raise ValueError('lcer.protocol_identity_mismatch')
        self._startup_raw = startup_raw
        requested = parse_stored_json(self._launch_raw)
        process, observer = self.process, self.observer
        # Keep the original child unreaped throughout the kernel/file reads.
        # Other wait/signal operations cannot release its PID in this window.
        # The transport reader does not acquire this lock and keeps draining.
        with process._wait_lock:
            if process._poll_unlocked() is not None:
                raise ValueError('lcer.process_state_changed')
            identity = observer._owned(process.pid, process.birth)
            paths = observer.paths(process.pid, process.birth)
            argv, environment = observer.launch_inputs(process.pid, process.birth)
            if (startup['pid'] != identity['pid'] or startup['cwd_realpath'] != paths['cwd_realpath'] or
                    paths != {key: requested[key] for key in ('cwd_realpath', 'executable_realpath')} or
                    argv != requested['argv'] or environment != requested['environment']):
                raise ValueError('lcer.process_input_invalid')
            executable = external_file_identity(paths['executable_realpath'])
            descriptors = observer.checked_descriptors(process.pid, process.birth)
            open_files = {}
            for row in descriptors:
                if row['kind'] == 'vnode':
                    file = external_file_identity(row['path'])
                    prior = open_files.setdefault(file['realpath'], file)
                    if prior != file:
                        raise ValueError('lcer.external_input_changed')
            mapped = observer.image_mappings(process.pid, process.birth)
            images = reconcile_process_images(startup['loaded_images'], mapped,
                                              parse_stored_json(self._cache_raw),
                                              observer.architecture(process.pid, process.birth))
            record = {**identity, 'cwd_realpath': paths['cwd_realpath'], 'executable': executable,
                      'argv': argv, 'environment': environment, 'descriptors': descriptors,
                      'open_files': [open_files[path] for path in sorted(open_files)],
                      'loaded_images': images, 'startup': startup}
            self.validator.validate('process_observation', record)
            if self._runtime_inputs is not None:
                self._runtime_inputs.validate_observation(record)
            # Re-read independently. A previous receipt is never the source
            # for a later process, descriptor, image or launch observation.
            if (observer._owned(process.pid, process.birth) != identity or
                    observer.paths(process.pid, process.birth) != paths or
                    observer.launch_inputs(process.pid, process.birth) != (argv, environment) or
                    observer.checked_descriptors(process.pid, process.birth) != descriptors or
                    observer.image_mappings(process.pid, process.birth) != mapped or
                    external_file_identity(paths['executable_realpath']) != executable):
                raise ValueError('lcer.process_observation_changed')
            for file in record['open_files']:
                if external_file_identity(file['realpath']) != file:
                    raise ValueError('lcer.external_input_changed')
            if process._poll_unlocked() is not None:
                raise ValueError('lcer.process_state_changed')
        return record

    def snapshot(self, checkpoint):
        """Read a fresh fault-state sample without consuming a schedule slot.

        The caller retains this row inside the fault event. It is an actual
        observation, never a copy of the preceding checkpoint or binding.
        """
        if self._failed and checkpoint not in ('terminal', 'cleanup'):
            raise ValueError('lcer.operation_sequence_invalid')
        row = {'checkpoint': checkpoint, 'domain': self._routing[1], 'launch_id': self._routing[2],
               'poll_returncode': None, 'observed_process': None, 'pipe_endpoints': [], 'pipe_holders': []}
        self.validator.validate('liveness', row)
        self._verify_original()
        before = self.process.observe_original_holders()
        observed = self._observe_process() if before['poll_returncode'] is None else None
        after = self.process.observe_original_holders()
        if before != after:
            raise ValueError('lcer.process_state_changed')
        if observed is not None:
            original = [item for item in after['pipe_endpoints'] if item['pid'] == self.process.pid]
            actual = [item for item in observed['descriptors'] if item['fd'] in (0, 1, 2)]
            if actual != sorted(original, key=lambda item: item['fd']):
                raise ValueError('lcer.original_pipe_identity_mismatch')
        self._verify_original()
        row.update(after, observed_process=observed)
        self.validator.validate('liveness', row)
        return parse_stored_json(stored_json_bytes(row))

    def sample(self, checkpoint):
        """Append one fresh liveness sample, including actual death and pipes."""
        if (checkpoint in self._checkpoints or
                'cleanup' in self._checkpoints or
                ('terminal' in self._checkpoints and checkpoint != 'cleanup') or
                (self._failed and checkpoint not in ('terminal', 'cleanup'))):
            raise ValueError('lcer.operation_sequence_invalid')
        self.validator.validate('liveness', {'checkpoint': checkpoint, 'domain': self._routing[1], 'launch_id': self._routing[2],
                                           'poll_returncode': None, 'observed_process': None, 'pipe_endpoints': [], 'pipe_holders': []})
        self._checkpoints.add(checkpoint)
        try:
            row = self.snapshot(checkpoint)
            if row['observed_process'] is not None:
                self.connection.trace.append('process_observation', row['observed_process'], self._routing[1], None)
            self.connection.trace.append('liveness', row, self._routing[1], None)
            return parse_stored_json(stored_json_bytes(row))
        except BaseException:
            self._failed = True
            raise


class AcquisitionProcessCohort:
    """Own the original processes, streams and cleanup for one frozen case.

    The case runner still owes build/source authorization, startup-world
    validation before binding, terminal census and complete case acceptance.
    This owner returns observed process facts and cleanup errors, not claims.
    """

    DOMAINS = ('domain_A', 'domain_B')

    def __init__(self, workspace, case_id, cache, budget, runtime_inputs=None):
        if not isinstance(workspace, AcquisitionWorkspace) or not workspace._reserved:
            raise ValueError('lcer.operation_sequence_invalid')
        if runtime_inputs is not None and (not isinstance(runtime_inputs, RuntimeBuildInputInventory)
                or runtime_inputs._build._workspace is not workspace or runtime_inputs.cache != cache):
            raise ValueError('lcer.runtime_build_capture_missing')
        self._runtime_inputs = runtime_inputs
        self.workspace = workspace
        self.case_id = select_frozen_case(workspace._contract_raw, case_id)['id']
        self._contract_raw = workspace._contract_raw
        self._cache_raw = stored_json_bytes(cache)
        self._budget = budget
        self._entries = {}
        self._launch_attempted = False
        self._startup_attempted = False
        self._ready = False
        self._replacement_attempted = False
        self._terminations = set()
        self._closing = False
        self._closed = False
        self._cleanup_result = None
        workspace.begin_case(case_id)
        self.trace = RawTraceWriter(self._contract_raw, workspace._output_root / case_id / 'harness.jsonl')

    @staticmethod
    def _timeout(value):
        if type(value) not in (int, float) or not 0 < value <= 60:
            raise ValueError('lcer.operation_sequence_invalid')
        return value

    def _launch(self, domain, replacement=False):
        launch = self.workspace.prepare_launch(self.case_id, domain, replacement=replacement)
        label = 'replacement' if replacement else domain
        process = OriginalPipeProcess(MacProcessObserver())
        # Register the object before spawn. A partially successful launch must
        # remain owned if validation, monitor setup or resume then fails.
        entry = {'launch': launch, 'process': process, 'monitor': None, 'connection': None, 'evidence': None}
        self._entries[label] = entry
        process.start(launch['argv'], launch['environment'], launch['cwd'])
        directory = self.workspace._output_root / self.case_id
        monitor = OriginalPipeMonitor(process, directory / (label + '.stdout.log'),
                                      directory / (label + '.stderr.log'), self._budget)
        entry['monitor'] = monitor
        connection = OriginalProtocolConnection(self._contract_raw, self.case_id, domain, launch['launch_id'], monitor, self.trace)
        entry['connection'] = connection
        inputs = {} if self._runtime_inputs is None else {'runtime_inputs': self._runtime_inputs}
        entry['evidence'] = OriginalProcessEvidence(self._contract_raw, connection, parse_stored_json(self._cache_raw), **inputs)
        monitor.start()
        process.resume()
        return entry

    def start_originals(self):
        if self._launch_attempted or self._closing:
            raise ValueError('lcer.operation_sequence_invalid')
        self.workspace.verify()
        self._launch_attempted = True
        for domain in self.DOMAINS:
            self._launch(domain)

    def read_startups(self, timeout=60):
        timeout = self._timeout(timeout)
        if (self._startup_attempted or self._closing or
                any(domain not in self._entries or self._entries[domain]['connection'] is None for domain in self.DOMAINS)):
            raise ValueError('lcer.operation_sequence_invalid')
        self._startup_attempted = True
        result = {}
        for domain in self.DOMAINS:
            result[domain] = self._entries[domain]['connection'].read_startup(timeout)
        self._ready = True
        return parse_stored_json(stored_json_bytes(result))

    def connection(self, domain):
        if domain not in self.DOMAINS or not self._ready or self._closing:
            raise ValueError('lcer.operation_sequence_invalid')
        return self._entries[domain]['connection']

    def launch_record(self, domain):
        if domain not in self.DOMAINS or domain not in self._entries:
            raise ValueError('lcer.operation_sequence_invalid')
        return parse_stored_json(stored_json_bytes(self._entries[domain]['launch']))

    def sample(self, domain, checkpoint):
        self.connection(domain)
        self.workspace.verify()
        return self._entries[domain]['evidence'].sample(checkpoint)

    def is_alive(self, domain):
        self.connection(domain)
        return self._entries[domain]['process'].poll() is None

    def start_replacement(self, timeout=60):
        timeout = self._timeout(timeout)
        if (self.case_id != 'F07' or not self._ready or self._closing or self._replacement_attempted or
                self._entries['domain_A']['process'].poll() is None):
            raise ValueError('lcer.operation_sequence_invalid')
        self.workspace.verify()
        self._replacement_attempted = True
        entry = self._launch('domain_A', replacement=True)
        # The replacement has no public command route. Identity detection may
        # inspect its startup; no bind or materialize can follow through this
        # owner. The original domain_A connection remains the original object.
        startup = entry['connection'].read_startup(timeout)
        return {'launch': parse_stored_json(stored_json_bytes(entry['launch'])), 'startup': startup}

    def fault_snapshot(self, domain, checkpoint, replacement=False):
        self.connection(domain)
        if type(replacement) is not bool or (replacement and (self.case_id != 'F07' or domain != 'domain_A')):
            raise ValueError('lcer.operation_sequence_invalid')
        label = 'replacement' if replacement else domain
        if label not in self._entries:
            raise ValueError('lcer.operation_sequence_invalid')
        self.workspace.verify()
        return self._entries[label]['evidence'].snapshot(checkpoint)

    def terminate_original(self, domain, timeout=60):
        """Perform only the four declared parent-owned process fault actions."""
        timeout = self._timeout(timeout)
        self.connection(domain)
        allowed = {'F07': 'domain_A', 'F08': 'domain_B', 'F11': 'domain_A', 'F12': 'domain_B'}
        if allowed.get(self.case_id) != domain or domain in self._terminations:
            raise ValueError('lcer.operation_sequence_invalid')
        self.workspace.verify()
        self._terminations.add(domain)
        process = self._entries[domain]['process']
        if process.poll() is not None or not process.send_signal(signal.SIGTERM):
            raise ValueError('lcer.original_process_exited')
        try:
            return process.wait(timeout)
        except TimeoutError:
            process.send_signal(signal.SIGKILL)
            return process.wait(timeout)

    def cleanup(self, timeout=60):
        timeout = self._timeout(timeout)
        if self._closed:
            return parse_stored_json(stored_json_bytes(self._cleanup_result))
        if self._closing:
            raise ValueError('lcer.operation_sequence_invalid')
        self._closing = True
        result = {'processes': [], 'liveness': [], 'errors': []}

        def failure(label, stage, error):
            result['errors'].append({'process': label, 'stage': stage,
                                     'exception': type(error).__name__, 'code': str(error)})

        # Keep all handles through exit, drainage and the final pipe census.
        # One failed process must not prevent cleanup of its surviving peer.
        for label, entry in self._entries.items():
            process, monitor, connection = entry['process'], entry['monitor'], entry['connection']
            row = {'process': label, 'pid': process.pid, 'poll_returncode': None,
                   'shutdown_requested': False, 'kill_sent': False, 'streams': None}
            result['processes'].append(row)
            if process.pid is None:
                try:
                    process.close_pipes()
                except Exception as error:
                    failure(label, 'close', error)
                continue
            try:
                if (process.poll() is None and label != 'replacement' and connection is not None and
                        connection.startup_raw is not None and connection.binding_sha256 is not None and
                        not connection._failed and not connection._shutdown):
                    row['shutdown_requested'] = True
                    response = connection.request('shutdown', 'shutdown_0001', timeout=timeout)
                    if response['response']['status'] != 'ok':
                        raise ValueError(response['response']['error']['underlying_code'])
            except Exception as error:
                failure(label, 'shutdown', error)
            try:
                try:
                    row['poll_returncode'] = process.wait(timeout)
                except TimeoutError:
                    row['kill_sent'] = process.send_signal(signal.SIGKILL)
                    row['poll_returncode'] = process.wait(timeout)
            except Exception as error:
                failure(label, 'wait', error)
            try:
                if monitor is not None and monitor._started:
                    row['streams'] = monitor.finish(timeout)
            except Exception as error:
                failure(label, 'drain', error)
            try:
                if entry['evidence'] is not None:
                    result['liveness'].append(entry['evidence'].sample('cleanup'))
                elif process.exec_descriptors is not None:
                    # No fabricated liveness row for an incomplete startup.
                    # Retain the real holder check; the case remains failed.
                    process.observe_original_holders()
            except Exception as error:
                failure(label, 'cleanup_liveness', error)
            finally:
                try:
                    process.close_pipes()
                    if monitor is not None and monitor._started and monitor._thread.is_alive():
                        monitor._thread.join(timeout)
                        if monitor._thread.is_alive():
                            raise TimeoutError('lcer.pipe_drain_timeout')
                except Exception as error:
                    failure(label, 'close', error)
        self._cleanup_result = parse_stored_json(stored_json_bytes(result))
        self._closed = True
        return parse_stored_json(stored_json_bytes(self._cleanup_result))


def process_binding_from_observation(contract_raw, startup_raw, observation, project,
                                     process_root, operator_user):
    """Construct the declared binding from checked records, without sending it.

    Callers still owe actual build/inventory, world and original-holder
    acceptance. This function checks record relations and derives digests;
    it cannot turn supplied records into an observation or a bind permission.
    """
    validator = FrozenWireValidator(contract_raw)
    policy = FrozenObligationPlanCompiler(contract_raw).compile()['constitutional_policy']
    startup = validator.parse('startup', startup_raw)
    observation = validator.parse('process_observation', stored_json_bytes(observation))
    project = validator.parse('file_identity', stored_json_bytes(project))
    if type(process_root) is not str:
        raise ValueError('lcer.process_input_invalid')
    root = Path(process_root)
    repository = '/Users/boandersson/Projects/CITY'
    if (not root.is_absolute() or str(root) != process_root or
            '..' in root.parts or type(operator_user) is not str or not operator_user or
            observation['startup'] != startup or observation['pid'] <= 0 or observation['ppid'] <= 0 or
            startup['pid'] != observation['pid'] or
            startup['cwd_realpath'] != observation['cwd_realpath'] or observation['cwd_realpath'] != repository or
            project['realpath'] != repository + '/' + policy['runtime']['project'] or
            project['sha256'] != policy['unchanged_dependencies'][policy['runtime']['project']]):
        raise ValueError('lcer.process_input_invalid')
    arguments = {'engine': policy['runtime']['engine'], 'absolute_city_project': project['realpath'],
                 'absolute_domain_root': process_root, 'observed_operator_user': operator_user,
                 **{key: startup[key] for key in ('witness_id', 'domain', 'launch_id')}}
    if (observation['argv'] != [item.format_map(arguments) for item in policy['launch_argv']] or
            observation['environment'] != {key: item.format_map(arguments)
                                          for key, item in policy['launch_environment'].items()} or
            observation['executable']['realpath'] != policy['runtime']['engine'] or
            observation['loaded_images'] != startup['loaded_images']):
        raise ValueError('lcer.process_input_invalid')
    for values in (startup['loaded_images'], startup['enabled_plugins'], startup['config_files']):
        names = [row['realpath'] for row in values]
        if (not names or names != sorted(set(names)) or
                any(not Path(name).is_absolute() or str(Path(name)) != name or '..' in Path(name).parts for name in names)):
            raise ValueError('lcer.process_input_invalid')
    if startup['proof_module'] not in startup['loaded_images'] or startup['proof_module']['source'] != 'dyld':
        raise ValueError('lcer.process_input_invalid')
    descriptors = observation['descriptors']
    numbers = [row['fd'] for row in descriptors]
    proof = [row for row in descriptors if row['fd'] in (0, 1, 2)]
    if (numbers != sorted(set(numbers)) or any(row['pid'] != observation['pid'] for row in descriptors) or
            [row['fd'] for row in proof] != [0, 1, 2] or
            any(row['kind'] != 'pipe' or row['path'] is not None or row['peer_kernel_id'] is None or
                row['access'] != ('read' if row['fd'] == 0 else 'write') for row in proof) or
            len({value for row in proof for value in (row['kernel_id'], row['peer_kernel_id'])}) != 6):
        raise ValueError('lcer.original_pipe_identity_mismatch')
    identities = {key: startup[key] for key in ('loaded_images', 'enabled_plugins', 'config_files', 'proof_module')}
    binding = {key: startup[key] for key in ('witness_id', 'domain', 'launch_id', 'pid')}
    binding.update(macos_birth_tuple=observation['macos_birth_tuple'],
                   executable_realpath=observation['executable']['realpath'],
                   executable_sha256=observation['executable']['sha256'],
                   project_realpath=project['realpath'], project_sha256=project['sha256'],
                   process_root_realpath=process_root, startup_sha256=hashlib.sha256(startup_raw).hexdigest())
    for key, value in (('module_inventory', observation['loaded_images']), ('argv', observation['argv']),
                       ('environment', observation['environment']), ('descriptor_map', proof),
                       ('cwd', observation['cwd_realpath']), ('input_inventory', identities)):
        binding[key + '_sha256'] = hashlib.sha256(stored_json_bytes(value)).hexdigest()
    validator.validate('process_binding', binding)
    return parse_stored_json(stored_json_bytes(binding))


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
    validate_python_import_paths(repo_root)
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
        # The preceding source-only path check excludes local caches. Ignore
        # macOS's external bytecode cache for these authenticated imports.
        sys.dont_write_bytecode = True
        sys.pycache_prefix = None
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


class CapturedCanonicalExecution:
    """Feed retained capture bytes into the frozen canonical call sequence.

    The acquisition owner still owes process, physical-world and liveness
    acceptance. This adapter never creates Q or a physical receipt, and its
    canonical result alone confers no live or synchronized representation claim.
    """

    def __init__(self, contract_raw, case_id, trace, proof_root=PROOF_ROOT):
        self._raw = contract_raw
        self._core = CanonicalRoundTrip(contract_raw, case_id, proof_root)
        self._case = select_frozen_case(contract_raw, case_id)
        self._validator = FrozenWireValidator(contract_raw)
        self._trace = trace
        self._captures = {}
        self._bindings = {}
        self._admitted = {}
        self._constructed = None
        self._call_count = 0
        self._terminal = False

    @property
    def head_raw(self):
        return self._core.head_raw

    @property
    def publication_count(self):
        return self._core.publication_count

    def retain_binding(self, binding):
        self._validator.validate('process_binding', binding)
        domain = binding['domain']
        if (binding['witness_id'] != self._case['id'] or domain in self._bindings
                or self._call_count or self._terminal):
            raise ValueError('lcer.operation_sequence_invalid')
        self._bindings[domain] = stored_json_bytes(binding)

    def materialize_input(self, domain, operation_id):
        if domain not in self._bindings or self._terminal:
            raise ValueError('lcer.operation_sequence_invalid')
        if operation_id == 'materialize_0001' and self.publication_count == 0:
            role, generation = 'R0', 0
        elif operation_id == 'materialize_0002' and self.publication_count == 1:
            role, generation = 'R1', 1
        else:
            raise ValueError('lcer.committed_record_required')
        binding = parse_stored_json(self._bindings[domain])
        record = parse_stored_json(self.head_raw)
        projection = {key: binding[key] for key in ('witness_id', 'domain', 'launch_id')}
        projection.update(schema='city.live_evidence_projection.v1', operation_id=operation_id,
                          binding_sha256=hashlib.sha256(self._bindings[domain]).hexdigest(),
                          record_role=role, record_raw_sha256=hashlib.sha256(self.head_raw).hexdigest(),
                          record_canonical_hash=self._core._canonical.canonical_hash(record),
                          generation=generation, allocation_owner=record['current_causal_state']['shared_slot']['allocation_owner'])
        payload = {'projection': projection, 'record_raw_utf8': self.head_raw.decode('utf-8'),
                   'launch_receipt_raw_utf8': (stored_json_bytes(self._core._canonical.launch_receipt(record)).decode('utf-8')
                                              if generation == 0 else None)}
        self._validator.validate('materialize_input', payload)
        return payload

    def retain_capture(self, domain, raw):
        if (domain not in self._bindings or domain in self._captures or self._terminal
                or self._call_count or self.publication_count):
            raise ValueError('lcer.operation_sequence_invalid')
        capture = self._validator.parse('emission_result', raw)
        binding = parse_stored_json(self._bindings[domain])
        expected_routing = {key: binding[key] for key in ('witness_id', 'domain', 'launch_id')}
        expected_routing.update(operation_id='emit_0001', binding_sha256=hashlib.sha256(self._bindings[domain]).hexdigest())
        for item in (capture['wrapper'], capture['physical_event']):
            if any(item[key] != value for key, value in expected_routing.items()):
                raise ValueError('lcer.binding_mismatch')
        q_raw = capture['q_raw_utf8'].encode('utf-8')
        if q_raw != self._core._original_q[domain]:
            raise ValueError('lcer.capture_bytes_invalid')
        q = parse_stored_json(q_raw)
        raw_hash = hashlib.sha256(q_raw).hexdigest()
        canonical_hash = self._core._canonical.q_hash(q)
        for item in (capture['wrapper'], capture['physical_event']):
            if (item['q_raw_sha256'] != raw_hash or item['q_canonical_hash'] != canonical_hash
                    or item['physical_event_id'] != q['physical_event_id'] or item['interaction_counter'] != 1):
                raise ValueError('lcer.capture_bytes_invalid')
        if (capture['physical_event']['accepted_record_raw_sha256'] != hashlib.sha256(self._core._r0).hexdigest()
                or capture['wrapper']['source_record_hash'] != self._core._canonical.canonical_hash(parse_stored_json(self._core._r0))):
            raise ValueError('lcer.capture_bytes_invalid')
        acceptance = parse_stored_json(capture['acceptance_receipt_raw_utf8'].encode('utf-8'))
        emission = parse_stored_json(capture['emission_receipt_raw_utf8'].encode('utf-8'))
        if (acceptance.get('process_instance_id') != binding['launch_id']
                or emission.get('process_instance_id') != binding['launch_id']):
            raise ValueError('lcer.binding_mismatch')
        canonical = self._core._canonical
        r0 = parse_stored_json(self._core._r0)
        if (stored_json_bytes(acceptance) != stored_json_bytes(canonical.materialization_acceptance_receipt(r0, domain, binding['launch_id']))
                or stored_json_bytes(emission) != stored_json_bytes(canonical.evidence_emission_receipt(r0, q, domain, binding['launch_id']))):
            raise ValueError('lcer.capture_bytes_invalid')
        self._captures[domain] = raw

    def next_call(self):
        """Run one actual predecessor call; retain its exact typed arguments."""
        sequence = _canonical_sequence(select_frozen_case(self._raw, self._case['id']))
        if (self._terminal or self._call_count >= len(sequence)
                or self._case != select_frozen_case(self._raw, self._case['id'])):
            raise ValueError('lcer.core_sequence_invalid')
        function, domain = sequence[self._call_count]
        canonical = self._core._canonical
        name = self._case['id']
        if function == 'admit_external_input_candidate':
            if domain not in self._captures:
                raise ValueError('lcer.capture_missing')
            capture = parse_stored_json(self._captures[domain])
            q = parse_stored_json(capture['q_raw_utf8'].encode('utf-8'))
            if self.publication_count == 0:
                if name == 'F03': q['target']['id'] = 'shared_slot_02'
                if name == 'F05': q['source']['source_record_hash'] = canonical.canonical_hash(parse_stored_json(self._core._r1))
                if name == 'F06': q['proposed_effect']['path'] = '/current_causal_state/forbidden_owner'
                if name in ('F03', 'F05', 'F06'):
                    del q['evidence']['evidence_digest']
                    q['evidence']['evidence_digest'] = canonical.evidence_digest(q)
            elif name == 'F10b':
                q['input_id'] = 'replay_probe_new_input'
            q_raw = stored_json_bytes(q)
            args = {'schema': 'city.live_evidence_admission_arguments.v1', 'record_raw_utf8': self.head_raw.decode('utf-8'),
                    'q_object_raw_utf8': q_raw.decode('utf-8'),
                    'q_raw_base64': base64.b64encode(q_raw[:-1] if name == 'F02' else q_raw).decode('ascii'),
                    'materialization_receipt_raw_utf8': capture['acceptance_receipt_raw_utf8'],
                    'emission_receipt_raw_utf8': capture['emission_receipt_raw_utf8']}
        elif function == 'construct_bext_from_sealed_fixture_set':
            order = self._case.get('witness', {}).get('presentation', ['domain_A', 'domain_B'])
            if name == 'F01': order = ['domain_A']
            if name == 'F04a': order = ['domain_A', 'domain_A']
            if any(key not in self._admitted for key in order):
                raise ValueError('lcer.core_sequence_invalid')
            members = [parse_stored_json(self._admitted[key]) for key in order]
            if name == 'F04b': members[1]['physical_event_id'] = members[0]['physical_event_id']
            args = {'schema': 'city.live_evidence_construction_arguments.v1', 'record_raw_utf8': self.head_raw.decode('utf-8'),
                    'fixture_raw_utf8': self._core._primary_fixture_raw.decode('utf-8'),
                    'presentation_members_raw_utf8': [stored_json_bytes(row).decode('utf-8') for row in members]}
        else:
            if self._constructed is None:
                raise ValueError('lcer.core_sequence_invalid')
            args = {'schema': 'city.live_evidence_resolution_arguments.v1', 'record_raw_utf8': self.head_raw.decode('utf-8'),
                    **parse_stored_json(self._constructed), 'fault_point': self._case.get('fault_point')}
        try:
            result, call = self._core.call(function, args)
        except Exception:
            self._terminal = True
            raise
        self._call_count += 1
        # A failed append is terminal even if the resolver already published.
        # Preserve the installed head; neither a log error nor a physical
        # failure is permission to recompute or roll it back.
        try:
            self._trace.append('canonical_call', call, domain, None)
        except Exception:
            self._terminal = True
            raise
        if call['exception_code'] is not None:
            self._terminal = True
        elif function == 'admit_external_input_candidate':
            self._admitted[domain] = call['return_raw_utf8'].encode('utf-8')
        elif function == 'construct_bext_from_sealed_fixture_set':
            self._constructed = call['return_raw_utf8'].encode('utf-8')
        return result, call

    def captures(self):
        return [{'domain': domain, 'emission': parse_stored_json(self._captures[domain]) if domain in self._captures else None}
                for domain in ('domain_A', 'domain_B')]


class LiveWorldAcceptance:
    """Parent-side world checks against an authenticated native class graph.

    The acquisition owner must derive class_parents from bound native inputs.
    A supplied graph or a successful fixture check is not acquisition evidence.
    The release verifier has its own raw-row implementation.
    """

    def __init__(self, contract_raw, class_parents):
        self.validator = FrozenWireValidator(contract_raw)
        self.policy = FrozenObligationPlanCompiler(contract_raw).compile()['constitutional_policy']
        self._parents_raw = stored_json_bytes(class_parents)
        self._runtime_inputs = None

    @classmethod
    def from_runtime_inputs(cls, contract_raw, runtime_inputs):
        if (not isinstance(runtime_inputs, RuntimeBuildInputInventory)
                or runtime_inputs.validator._contract_raw != contract_raw
                or runtime_inputs._build._workspace is None):
            raise ValueError('lcer.runtime_build_capture_missing')
        result = cls(contract_raw, {})
        result._runtime_inputs = runtime_inputs
        return result

    def _ancestry(self, name):
        parents = parse_stored_json(self._parents_raw)
        result = set()
        while name is not None:
            if type(name) is not str or name in result or name not in parents:
                raise ValueError('lcer.class_hierarchy_invalid')
            result.add(name)
            name = parents[name]
        return result

    def census(self, worlds):
        if self._runtime_inputs is not None:
            # The first original startup sample populates the actual loaded
            # inventory before startup-world acceptance or any bind command.
            self._parents_raw = stored_json_bytes(self._runtime_inputs.native_class_parents())
        all_rows, relevant, pawns, controllers = [], [], [], []
        world_names = set()
        actor_names = set()
        for world in worlds:
            self.validator.validate('world_row', world)
            path = world['world_path']
            size, nulls, actors = world['actor_array_size'], world['null_slots'], world['actors']
            names = [row['actor_path'] for row in actors]
            if (path in world_names or world['visited_slots'] != list(range(size))
                    or len(nulls) != len(set(nulls)) or any(slot >= size for slot in nulls)
                    or len(actors) + len(nulls) != size or names != sorted(set(names))):
                raise ValueError('lcer.world_census_invalid')
            world_names.add(path)
            for actor in actors:
                if (actor['world_path'] != path or not actor['actor_path'].startswith(path + ':')
                        or actor['actor_id'] != path + '|' + actor['actor_path']
                        or actor['actor_id'] in actor_names):
                    raise ValueError('lcer.world_census_invalid')
                actor_names.add(actor['actor_id'])
                ancestry = self._ancestry(actor['class_path'])
                proof = '/Script/CityLiveEvidenceProof.CityLiveEvidenceActor' in ancestry
                old = actor['class_path'].split('.', 1)[0] == '/Script/CityMaterializationProof'
                if not proof and any(actor[key] is not None for key in
                                     ('role', 'domain', 'generation', 'record_raw_sha256', 'allocation_owner')):
                    raise ValueError('lcer.world_census_invalid')
                if proof or old or actor['role'] in ('head_anchor', 'resource_state'):
                    relevant.append(actor)
                if '/Script/Engine.Pawn' in ancestry:
                    pawns.append(actor)
                if '/Script/Engine.Controller' in ancestry:
                    controllers.append(actor)
                all_rows.append(actor)
        games = [world for world in worlds if world['world_type'] == 'Game']
        selected = games[0] if len(games) == 1 else None
        wrong = (selected is None or selected['world_path'].split('.', 1)[0] != self.policy['runtime']['map']
                 or selected['game_mode_class'] != self.policy['runtime']['game_mode'])
        if selected is not None:
            wrong = wrong or any(row['world_path'] != selected['world_path'] for row in relevant)
        return {'world': selected, 'wrong_world': wrong, 'rows': all_rows, 'relevant': relevant,
                'pawns': pawns, 'controllers': controllers,
                'anchors': [row for row in relevant if row['role'] == 'head_anchor'],
                'resources': [row for row in relevant if row['role'] == 'resource_state']}

    def startup(self, startup):
        self.validator.validate('startup', startup)
        facts = self.census(startup['worlds'])
        if (facts['wrong_world'] or facts['relevant'] or facts['pawns'] or len(facts['controllers']) != 1
                or any(row['auto_receive_input'] != 0 for row in facts['rows'])):
            raise ValueError('lcer.startup_world_invalid')
        controller = facts['controllers'][0]
        if (controller['class_path'] != '/Script/Engine.PlayerController' or controller['pending_kill']
                or startup['controllers'] != [{'actor_path': controller['actor_path'],
                                               'class_path': controller['class_path'], 'pawn_path': None}]):
            raise ValueError('lcer.startup_world_invalid')
        return facts

    def representation(self, observation, record_raw, generation, domain):
        self.validator.validate('live_observation', observation)
        facts = self.census(observation['worlds'])
        rows, anchors, resources = facts['relevant'], facts['anchors'], facts['resources']
        if facts['wrong_world']:
            raise ValueError('lcer.live_world_mismatch')
        if any(row['generation'] != generation for row in rows):
            raise ValueError('lcer.live_generation_mismatch')
        if (len(rows) != 2 or len(anchors) != 1 or len(resources) != 1
                or any(row['pending_kill'] or row['class_path'].split('.', 1)[0] == '/Script/CityMaterializationProof'
                       for row in rows)):
            raise ValueError('lcer.live_actor_cardinality_mismatch')
        record_hash = hashlib.sha256(record_raw).hexdigest()
        if any(row['record_raw_sha256'] != record_hash or row['domain'] != domain for row in rows):
            raise ValueError('lcer.live_record_domain_mismatch')
        owner = parse_stored_json(record_raw)['current_causal_state']['shared_slot']['allocation_owner']
        if anchors[0]['allocation_owner'] is not None or resources[0]['allocation_owner'] != owner:
            raise ValueError('lcer.live_owner_mismatch')
        summary = {'selected_world_path': facts['world']['world_path'], 'anchor_count': 1, 'resource_actor_count': 1,
                   'all_proof_actor_ids': sorted(row['actor_id'] for row in rows), 'record_sha256': record_hash,
                   'generation': generation, 'allocation_owner': owner}
        if any(stored_json_bytes(observation[key]) != stored_json_bytes(value) for key, value in summary.items()):
            raise ValueError('lcer.live_summary_mismatch')
        return facts

    def check_summary(self, observation, facts):
        """Check reported summaries even when the physical state is invalid."""
        self.validator.validate('live_observation', observation)
        def homogeneous(rows, key):
            values = {row[key] for row in rows}
            return next(iter(values)) if len(values) == 1 else None
        summary = {'selected_world_path': None if facts['world'] is None else facts['world']['world_path'],
                   'anchor_count': len(facts['anchors']), 'resource_actor_count': len(facts['resources']),
                   'all_proof_actor_ids': sorted(row['actor_id'] for row in facts['relevant']),
                   'record_sha256': homogeneous(facts['relevant'], 'record_raw_sha256'),
                   'generation': homogeneous(facts['relevant'], 'generation'),
                   'allocation_owner': homogeneous(facts['resources'], 'allocation_owner')}
        if any(stored_json_bytes(observation[key]) != stored_json_bytes(value) for key, value in summary.items()):
            raise ValueError('lcer.live_summary_mismatch')


class CasePrefixExecution:
    """Execute the frozen prefixes, failure action and terminal census.

    Source/build authorization, authenticated native input derivation, cleanup
    and complete release construction remain the enclosing runner's duties.
    This component returns no phase, release or live-acceptance claim.
    """

    DOMAINS = ('domain_A', 'domain_B')

    def __init__(self, cohort, world_acceptance):
        if not isinstance(cohort, AcquisitionProcessCohort) or not isinstance(world_acceptance, LiveWorldAcceptance):
            raise ValueError('lcer.operation_sequence_invalid')
        self.cohort = cohort
        self.workspace = cohort.workspace
        self._raw = cohort._contract_raw
        self.case = select_frozen_case(self._raw, cohort.case_id)
        self.world = world_acceptance
        self.validator = FrozenWireValidator(self._raw)
        self.trace = cohort.trace
        self.canonical = CapturedCanonicalExecution(self._raw, cohort.case_id, self.trace,
                                                     proof_root=self.workspace._repository_root / 'proof_kernel')
        self._prefix = -1
        self._failed = False
        self._running = False
        self._failure_attempted = False
        self._failure_code = None
        self._terminal_attempted = False
        self._terminal_capture = None
        self._case_attempted = False
        self._case_result = None
        self._wire_faults = []
        self._deadline = time.monotonic() + 900
        self._bindings = {}
        self._receipts = {}
        self._represented = {}
        self._observations = {}
        self._dispositions = {domain: 'unclaimed' for domain in self.DOMAINS}
        self._initial_raw = self.canonical.head_raw

    def _timeout(self):
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('lcer.case_timeout')
        return min(60, remaining)

    def _head_event(self, edge, domain=None, disposition='unclaimed', observation=None):
        self.trace.append('head_event', {'edge': edge, 'canonical_role': 'R1' if self.canonical.publication_count else 'R0',
                                        'canonical_raw_utf8': self.canonical.head_raw.decode('utf-8'),
                                        'domain': domain, 'disposition': disposition,
                                        'observation_sha256': None if observation is None else hashlib.sha256(stored_json_bytes(observation)).hexdigest()},
                          domain, None)
        if domain is not None:
            self._dispositions[domain] = disposition

    def _request(self, domain, command, operation_id, payload=None):
        self.workspace.verify()
        result = self.cohort.connection(domain).request(command, operation_id, payload, timeout=self._timeout())
        self._wire_faults.extend(result.get('fault_events', []))
        response = result['response']
        if response['status'] != 'ok':
            raise ValueError(response['error']['underlying_code'])
        return response['payload']

    def _live(self, checkpoint):
        # Retain both observations before evaluating their joint guard. A
        # failed first original cannot hide the peer's actual sample.
        samples = [self.cohort.sample(domain, checkpoint) for domain in self.DOMAINS]
        for row in samples:
            binding = self._bindings[row['domain']]
            process = row['observed_process']
            if row['poll_returncode'] is not None:
                raise ValueError('lcer.original_process_exited')
            if (process is None or process['pid'] != binding['pid']
                    or process['macos_birth_tuple'] != binding['macos_birth_tuple']
                    or row['launch_id'] != binding['launch_id']):
                raise ValueError('lcer.original_process_identity_mismatch')
        return samples

    def _materialize(self, domain, operation):
        payload = self.canonical.materialize_input(domain, operation)
        receipt = self._request(domain, 'materialize', operation, payload)
        self.validator.validate('materialization_result', receipt)
        binding = self._bindings[domain]
        projection = payload['projection']
        if operation == 'materialize_0001':
            expected = self.canonical._core._canonical.materialization_acceptance_receipt(
                parse_stored_json(self._initial_raw), domain, binding['launch_id'])
            if (receipt['r1_representation'] is not None or
                    receipt['r0_acceptance_raw_utf8'] != stored_json_bytes(expected).decode('utf-8')):
                raise ValueError('lcer.materialization_receipt_invalid')
        else:
            r1 = receipt['r1_representation']
            if receipt['r0_acceptance_raw_utf8'] is not None or r1 is None:
                raise ValueError('lcer.materialization_receipt_invalid')
            if any(r1[key] != projection[key] for key in ('witness_id', 'domain', 'launch_id', 'operation_id',
                                                         'binding_sha256', 'record_raw_sha256', 'record_canonical_hash',
                                                         'generation', 'allocation_owner')):
                raise ValueError('lcer.materialization_receipt_invalid')
            if r1['anchor_actor_id'] == r1['resource_actor_id']:
                raise ValueError('lcer.materialization_receipt_invalid')
        self._receipts[domain] = stored_json_bytes(receipt)
        self._represented[domain] = (payload['record_raw_utf8'].encode('utf-8'), projection['generation'])

    def _inspect(self, checkpoint):
        # Complete both serialized censuses before accepting either world.
        observations = {domain: self._request(domain, 'inspect', 'inspect_' + checkpoint) for domain in self.DOMAINS}
        for domain, observation in observations.items():
            record, generation = self._represented[domain]
            facts = self.world.representation(observation, record, generation, domain)
            receipt = parse_stored_json(self._receipts[domain])
            r1 = receipt['r1_representation']
            if r1 is not None and (r1['anchor_actor_id'] != facts['anchors'][0]['actor_id']
                                   or r1['resource_actor_id'] != facts['resources'][0]['actor_id']):
                raise ValueError('lcer.materialization_receipt_invalid')
            disposition = 'current' if record == self.canonical.head_raw else 'stale'
            self._head_event('classify', domain, disposition, observation)
            self._observations[domain] = stored_json_bytes(observation)
        self._live(checkpoint)

    def _emit(self, domain):
        capture = self._request(domain, 'emit', 'emit_0001')
        previous = parse_stored_json(self._observations[domain])
        record, generation = self._represented[domain]
        facts = self.world.representation(previous, record, generation, domain)
        if capture['physical_event']['actor_id'] != facts['resources'][0]['actor_id']:
            raise ValueError('lcer.protocol_event_mismatch')
        if capture['acceptance_receipt_raw_utf8'] != parse_stored_json(self._receipts[domain])['r0_acceptance_raw_utf8']:
            raise ValueError('lcer.materialization_receipt_invalid')
        self.canonical.retain_capture(domain, stored_json_bytes(capture))

    def _canonical_call(self):
        self._timeout()
        result, call = self.canonical.next_call()
        if call['exception_code'] is not None:
            raise ValueError(call['exception_code'])
        return result, call

    @staticmethod
    def _fault_bytes(kind, raw):
        return {'kind': 'bytes', 'semantic_type': kind, 'raw_base64': base64.b64encode(raw).decode('ascii')}

    def _retain_fault(self, program, before, after, code, operation=None):
        event = {key: program[key] for key in ('executor', 'stage', 'action')}
        event.update(failure_case=program['id'], consumed=True, underlying_code=code, before=before, after=after)
        self.trace.append('fault_event', event, program['domain'], operation)
        return event

    def _canonical_failure(self, program):
        if program['id'] == 'F01':
            self._emit('domain_A')
        while True:
            self._timeout()
            _, call = self.canonical.next_call()
            if call['exception_code'] is not None:
                break
        after = call['arguments']
        before = parse_stored_json(stored_json_bytes(after))
        if call['function'] == 'admit_external_input_candidate':
            capture = parse_stored_json(self.canonical._captures[program['domain']])
            before['q_object_raw_utf8'] = capture['q_raw_utf8']
            before['q_raw_base64'] = base64.b64encode(capture['q_raw_utf8'].encode('utf-8')).decode('ascii')
            kind = 'admission_arguments'
        else:
            kind = 'construction_arguments'
            if program['id'] != 'F01':
                before['presentation_members_raw_utf8'] = [self.canonical._admitted[domain].decode('utf-8') for domain in self.DOMAINS]
        self._retain_fault(program, self._fault_bytes(kind, stored_json_bytes(before)),
                           self._fault_bytes(kind, stored_json_bytes(after)), call['exception_code'])
        return call['exception_code']

    def _fault_record_input(self, domain, record_raw, generation):
        core = self.canonical._core
        if record_raw != (core._r0 if generation == 0 else core._r1) or generation not in (0, 1):
            raise ValueError('lcer.committed_record_required')
        binding = self._bindings[domain]
        record = parse_stored_json(record_raw)
        projection = {key: binding[key] for key in ('witness_id', 'domain', 'launch_id')}
        projection.update(schema='city.live_evidence_projection.v1', operation_id='materialize_0002',
                          binding_sha256=hashlib.sha256(stored_json_bytes(binding)).hexdigest(),
                          record_role='R0' if generation == 0 else 'R1', record_raw_sha256=hashlib.sha256(record_raw).hexdigest(),
                          record_canonical_hash=core._canonical.canonical_hash(record), generation=generation,
                          allocation_owner=record['current_causal_state']['shared_slot']['allocation_owner'])
        payload = {'projection': projection, 'record_raw_utf8': record_raw.decode('utf-8'),
                   'launch_receipt_raw_utf8': stored_json_bytes(core._canonical.launch_receipt(record)).decode('utf-8') if generation == 0 else None}
        self.validator.validate('materialize_input', payload)
        return payload

    def _materialize_command_bytes(self, domain, payload):
        binding = self._bindings[domain]
        command = {key: binding[key] for key in ('witness_id', 'domain', 'launch_id')}
        command.update(schema='city.live_evidence_command.v1', operation_id='materialize_0002', command='materialize',
                       binding_sha256=hashlib.sha256(stored_json_bytes(binding)).hexdigest(), payload=payload)
        self.validator.validate('command', command)
        return stored_json_bytes(command)

    def _command_failure(self, program):
        domain = program['domain']
        core = self.canonical._core
        before = self._fault_record_input(domain, core._r1, 1)
        after = parse_stored_json(stored_json_bytes(before))
        if program['id'] == 'F09':
            r0 = parse_stored_json(core._r0)
            working = core._canonical.working_state_projection(r0, r0['current_causal_state'], r0['future_causal_state'])
            after['record_raw_utf8'] = stored_json_bytes(working).decode('utf-8')
        elif program['id'] == 'F17':
            after = self._fault_record_input(domain, core._r0, 0)
        else:
            # F18's only mutation is made at the actual original pipe write.
            # OriginalProtocolConnection retains those exact before/after bytes.
            if program['id'] != 'F18':
                raise ValueError('lcer.operation_sequence_invalid')
        self.validator.validate('materialize_input', after)
        try:
            self._request(domain, 'materialize', 'materialize_0002', after)
        except ValueError as error:
            code = str(error)
        else:
            raise ValueError('lcer.expected_failure_missing')
        if program['id'] != 'F18':
            self._retain_fault(program, self._fault_bytes('materialize_command', self._materialize_command_bytes(domain, before)),
                               self._fault_bytes('materialize_command', self._materialize_command_bytes(domain, after)), code, 'materialize_0002')
        else:
            if len(self._wire_faults) != 1:
                raise ValueError('lcer.fault_event_invalid')
            event = self._wire_faults[0]
            self._check_fault_identity(program, event, code)
            expected = self._materialize_command_bytes(domain, before)
            changed = parse_stored_json(expected)
            changed['binding_sha256'] = '0' * 64
            if (event['before'] != self._fault_bytes('materialize_command', expected)
                    or event['after'] != self._fault_bytes('materialize_command', stored_json_bytes(changed))):
                raise ValueError('lcer.fault_event_invalid')
        return code

    def _process_failure(self, program):
        domain = program['domain']
        if program['id'] == 'F08':
            self._emit('domain_A')
        before = self.cohort.fault_snapshot(domain, 'terminal')
        if before['poll_returncode'] is not None or before['observed_process'] is None:
            raise ValueError('lcer.fault_precondition_invalid')
        self.cohort.terminate_original(domain, timeout=self._timeout())
        exited = self.cohort.fault_snapshot(domain, 'terminal')
        if exited['poll_returncode'] is None or exited['observed_process'] is not None:
            raise ValueError('lcer.fault_action_incomplete')
        if program['id'] == 'F07':
            replacement = self.cohort.start_replacement(timeout=self._timeout())
            after = self.cohort.fault_snapshot(domain, 'terminal', replacement=True)
            if after['poll_returncode'] is not None or after['observed_process'] is None:
                raise ValueError('lcer.fault_action_incomplete')
            self.world.startup(replacement['startup'])
            launch = replacement['launch']
            project = external_file_identity(self.workspace._repository_root / self.world.policy['runtime']['project'])
            new_binding = process_binding_from_observation(self._raw, stored_json_bytes(replacement['startup']),
                after['observed_process'], project, launch['process_root_realpath'], launch['environment']['USER'])
            original = self._bindings[domain]
            if (new_binding == original or new_binding['launch_id'] == original['launch_id']
                    or new_binding['process_root_realpath'] == original['process_root_realpath']
                    or new_binding['descriptor_map_sha256'] == original['descriptor_map_sha256']
                    or (new_binding['pid'], new_binding['macos_birth_tuple']) == (original['pid'], original['macos_birth_tuple'])):
                raise ValueError('lcer.fault_action_incomplete')
            code = 'lcer.original_process_identity_mismatch'
        else:
            after = exited
            code = 'lcer.original_process_exited'
        self._retain_fault(program, {'kind': 'process', 'sample': before}, {'kind': 'process', 'sample': after}, code)
        return code

    def _check_fault_identity(self, program, event, code):
        self.validator.validate('fault_event', event)
        if (event['failure_case'] != program['id'] or event['consumed'] is not True or event['underlying_code'] != code
                or any(event[key] != program[key] for key in ('executor', 'stage', 'action'))):
            raise ValueError('lcer.fault_event_invalid')

    def _child_failure(self, program):
        domain = program['domain']
        arm = {'failure_case': program['id'], 'stage': program['stage'], 'operation_id': 'materialize_0002'}
        ack = self._request(domain, 'arm_fault', 'arm_fault_0001', arm)
        if (ack['failure_case'] != program['id'] or ack['stage'] != program['stage'] or ack['armed_for'] != 'materialize_0002'):
            raise ValueError('lcer.fault_arm_invalid')
        try:
            self._materialize(domain, 'materialize_0002')
            self._inspect('L4')
        except ValueError as error:
            code = str(error)
        else:
            raise ValueError('lcer.expected_failure_missing')
        if len(self._wire_faults) != 1:
            raise ValueError('lcer.fault_event_invalid')
        event = self._wire_faults[0]
        self._check_fault_identity(program, event, code)
        if event['before']['kind'] != 'world' or event['after']['kind'] != 'world':
            raise ValueError('lcer.fault_event_invalid')
        before, after = event['before']['observation'], event['after']['observation']
        for observation in (before, after):
            binding = self._bindings[domain]
            if (any(observation[key] != binding[key] for key in ('domain', 'witness_id', 'launch_id'))
                    or observation['operation_id'] != 'materialize_0002'
                    or observation['binding_sha256'] != hashlib.sha256(stored_json_bytes(binding)).hexdigest()):
                raise ValueError('lcer.fault_event_invalid')
        old_facts, new_facts = self.world.census(before['worlds']), self.world.census(after['worlds'])
        self.world.check_summary(before, old_facts)
        self.world.check_summary(after, new_facts)
        if old_facts['wrong_world'] or new_facts['wrong_world']:
            raise ValueError('lcer.fault_event_invalid')
        r1 = self.canonical.head_raw
        if program['id'] in ('F13', 'F14'):
            if (before != after or new_facts['anchors'] or len(new_facts['relevant']) != 1
                    or len(new_facts['resources']) != 1):
                raise ValueError('lcer.fault_event_invalid')
            actor = new_facts['resources'][0]
            if (actor['generation'] != 1 or actor['domain'] != domain or actor['record_raw_sha256'] != hashlib.sha256(r1).hexdigest()
                    or actor['allocation_owner'] != 'domain_A' or actor['pending_kill']):
                raise ValueError('lcer.fault_event_invalid')
        else:
            self.world.representation(before, r1, 1, domain)
            old = {row['actor_id']: row for row in old_facts['rows']}
            new = {row['actor_id']: row for row in new_facts['rows']}
            if program['id'] == 'F15':
                resource = old_facts['resources'][0]['actor_id']
                expected = parse_stored_json(stored_json_bytes(before))
                for world in expected['worlds']:
                    for actor in world['actors']:
                        if actor['actor_id'] == resource:
                            actor['allocation_owner'] = 'domain_B'
                expected['allocation_owner'] = 'domain_B'
                if after != expected:
                    raise ValueError('lcer.fault_event_invalid')
            else:
                extra = set(new) - set(old)
                if len(extra) != 1 or any(new.get(key) != row for key, row in old.items()):
                    raise ValueError('lcer.fault_event_invalid')
                actor = new[extra.pop()]
                generation = 1 if program['id'] == 'F16a' else 0
                raw = r1 if generation else self._initial_raw
                if (actor not in new_facts['resources'] or actor['domain'] != domain or actor['generation'] != generation
                        or actor['record_raw_sha256'] != hashlib.sha256(raw).hexdigest()
                        or actor['allocation_owner'] != ('domain_A' if generation else None) or actor['pending_kill']):
                    raise ValueError('lcer.fault_event_invalid')
        return code

    def run_failure(self):
        """Perform the exact frozen action after its complete normal prefix.

        A matching code is only the action result. Terminal physical assertions,
        cleanup, independent verification and case acceptance remain required.
        """
        if (self._failed or self._running or self._failure_attempted or self.case['kind'] == 'witness'
                or self.case != select_frozen_case(self._raw, self.cohort.case_id)
                or self._prefix != int(self.case['prefix'][1])):
            raise ValueError('lcer.operation_sequence_invalid')
        self._failure_attempted = True
        self._running = True
        try:
            self._timeout()
            self.workspace.verify()
            if self.case['kind'] == 'canonical_fault':
                self._live('before_resolve')
                _, call = self.canonical.next_call()
                self._live('after_resolve')
                code, expected = call['exception_code'], self.case['underlying_code']
            else:
                program = self.case['failure_program']
                expected = program['underlying_code']
                if expected.startswith('concurrent_external_'):
                    code = self._canonical_failure(program)
                elif program['executor'] == 'unreal':
                    code = self._child_failure(program)
                elif program['id'] in ('F07', 'F08', 'F11', 'F12'):
                    code = self._process_failure(program)
                else:
                    code = self._command_failure(program)
            if code != expected or not self.canonical._core.canonical_coverage()['canonical_prefix_complete']:
                raise ValueError('lcer.unexpected_failure_outcome')
            self._failure_code = code
            return {'underlying_code': code, 'publication_count': self.canonical.publication_count,
                    'live_acceptance_verified': False}
        finally:
            # Neither a successful expected action nor a broken action permits
            # another normal command, canonical operation or fault attempt.
            self._running = False
            self._failed = True
            for domain in self.DOMAINS:
                self._dispositions[domain] = 'unclaimed'

    def capture_terminal(self):
        """Census surviving originals once and verify the frozen terminal state.

        All original handles and streams remain owned. The enclosing runner
        must still execute cohort cleanup and retain the completed raw files.
        """
        if (self._terminal_attempted or self._running or self._failure_code is None
                or self.case != select_frozen_case(self._raw, self.cohort.case_id)):
            raise ValueError('lcer.operation_sequence_invalid')
        self._terminal_attempted = True
        observations, samples, errors = {}, {}, []
        for domain in self.DOMAINS:
            try:
                if self.cohort.is_alive(domain):
                    observations[domain] = self._request(domain, 'inspect', 'inspect_terminal')
            except Exception as error:
                errors.append(error)
        for domain in self.DOMAINS:
            try:
                samples[domain] = self.cohort.sample(domain, 'terminal')
            except Exception as error:
                errors.append(error)
        if errors:
            raise errors[0]
        dead_domain = {'F07': 'domain_A', 'F08': 'domain_B', 'F11': 'domain_A', 'F12': 'domain_B'}.get(self.case['id'])
        program = self.case.get('failure_program')
        for domain in self.DOMAINS:
            sample = samples[domain]
            dead = sample['poll_returncode'] is not None
            if dead != (domain == dead_domain) or (sample['observed_process'] is None) != dead:
                raise ValueError('lcer.terminal_process_invalid')
            if dead:
                if domain in observations:
                    raise ValueError('lcer.terminal_process_invalid')
                self._head_event('terminal', domain, 'unavailable')
                continue
            process = sample['observed_process']
            binding = self._bindings[domain]
            if (process['pid'] != binding['pid'] or process['macos_birth_tuple'] != binding['macos_birth_tuple']
                    or sample['launch_id'] != binding['launch_id'] or domain not in observations):
                raise ValueError('lcer.terminal_process_invalid')
            observation = observations[domain]
            facts = self.world.census(observation['worlds'])
            self.world.check_summary(observation, facts)
            if facts['wrong_world']:
                raise ValueError('lcer.terminal_world_invalid')
            affected_child = program is not None and program['executor'] == 'unreal' and program['domain'] == domain
            if affected_child:
                event, = self._wire_faults
                after = self.world.census(event['after']['observation']['worlds'])
                if facts['relevant'] != after['relevant']:
                    raise ValueError('lcer.terminal_world_invalid')
                disposition = 'unavailable' if self.case['id'] in ('F13', 'F14') else 'unclaimed'
            else:
                self.world.representation(observation, self._initial_raw, 0, domain)
                disposition = 'stale' if self.canonical.publication_count else 'unclaimed'
            self._head_event('terminal', domain, disposition, observation)
        if not self.canonical._core.canonical_coverage()['canonical_prefix_complete']:
            raise ValueError('lcer.terminal_canonical_invalid')
        self._terminal_capture = stored_json_bytes({'observations': observations, 'liveness': samples,
            'underlying_code': self._failure_code, 'publication_count': self.canonical.publication_count,
            'live_acceptance_verified': False})
        return parse_stored_json(self._terminal_capture)

    def _closed_case_record(self, errors, cleanup):
        """Derive repeated fields from the closed original trace and streams."""
        policy = self.world.policy
        case_id = self.case['id']
        output = self.workspace._output_root
        targets = policy['artifact_hash_graph']['case_record_targets'][case_id]
        if {path.name for path in (output / case_id).iterdir()} != {Path(name).name for name in targets}:
            raise ValueError('lcer.case_artifact_membership_invalid')
        files, hashes = {}, []
        for relative in targets:
            path = output / relative
            if path.is_symlink() or path.resolve() != path or not path.is_file():
                raise ValueError('lcer.case_artifact_missing')
            identity = external_file_identity(path)
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != identity['sha256'] or len(raw) != identity['size_bytes']:
                raise ValueError('lcer.case_artifact_changed')
            files[relative] = raw
            hashes.append({'path': relative, 'sha256': identity['sha256'], 'size_bytes': identity['size_bytes']})
        rows = []
        previous = None
        for index, raw in enumerate(files[case_id + '/harness.jsonl'].splitlines(keepends=True)):
            event = self.validator.parse('trace_event', raw)
            self.validator.validate(event['event_id'], event['payload'])
            if event['sequence'] != index or event['previous_event_sha256'] != previous:
                raise ValueError('lcer.trace_relation_invalid')
            previous = hashlib.sha256(raw).hexdigest()
            rows.append(event)
        if rows != self.trace.rows():
            raise ValueError('lcer.trace_relation_invalid')
        bindings, captures, materializations, observations = {}, {}, [], []
        stdin, seen_stdout = {}, set()
        labels = {}
        for label, entry in self.cohort._entries.items():
            launch = entry['launch']
            labels[(launch['domain'], launch['launch_id'])] = label
        for event in rows:
            if event['event_id'] != 'wire_event':
                continue
            wire = event['payload']
            raw = wire['raw_line_utf8'].encode('utf-8')
            message = self.validator.parse(wire['parsed_schema'], raw)
            if wire['parsed_schema'] == 'fault_event':
                # Child fault records carry routing in their containing event.
                identity = (event['domain'], self.cohort._entries[event['domain']]['launch']['launch_id'])
            else:
                identity = (message['domain'], message['launch_id'])
            label = labels.get(identity)
            if label is None:
                raise ValueError('lcer.trace_relation_invalid')
            if wire['direction'] == 'stdin':
                if wire['parsed_schema'] != 'command' or label == 'replacement':
                    raise ValueError('lcer.trace_relation_invalid')
                retained = stdin.setdefault(label, bytearray())
                if wire['stream_byte_offset'] != len(retained):
                    raise ValueError('lcer.trace_relation_invalid')
                retained.extend(raw)
                if message['command'] == 'bind':
                    if message['domain'] in bindings:
                        raise ValueError('lcer.trace_relation_invalid')
                    bindings[message['domain']] = message['payload']
            else:
                relative = case_id + '/' + label + '.stdout.log'
                offset = wire['stream_byte_offset']
                if (relative not in files or (offset and files[relative][offset - 1:offset] != b'\n')
                        or files[relative][offset:offset + len(raw)] != raw or (relative, offset) in seen_stdout):
                    raise ValueError('lcer.trace_relation_invalid')
                seen_stdout.add((relative, offset))
                if wire['parsed_schema'] == 'response' and message['status'] == 'ok':
                    payload = message['payload']
                    self.validator.validate(policy['schema_contract']['response_match'][message['command']], payload)
                    if message['command'] == 'materialize':
                        materializations.append(payload)
                    elif message['command'] == 'inspect':
                        observations.append(payload)
                    elif message['command'] == 'emit':
                        if message['domain'] in captures:
                            raise ValueError('lcer.trace_relation_invalid')
                        captures[message['domain']] = payload
        scanned = set()
        for relative, raw in files.items():
            if not relative.endswith('.stdout.log'):
                continue
            offset = 0
            for line in raw.splitlines(keepends=True):
                if line.lstrip().startswith(b'{'):
                    parse_stored_json(line)
                    scanned.add((relative, offset))
                offset += len(line)
        if scanned != seen_stdout:
            raise ValueError('lcer.untraced_process_output')
        for label, entry in self.cohort._entries.items():
            monitor = entry['monitor']
            if monitor is not None and bytes(stdin.get(label, b'')) != monitor.stdin_bytes():
                raise ValueError('lcer.untraced_process_input')
        captured = [{'domain': domain, 'emission': captures.get(domain)} for domain in self.DOMAINS]
        canonical_calls = [row['payload'] for row in rows if row['event_id'] == 'canonical_call']
        if (canonical_calls != self.canonical._core.retained_calls() or captured != self.canonical.captures()
                or any(bindings.get(domain) != value for domain, value in self._bindings.items())):
            raise ValueError('lcer.trace_relation_invalid')
        expected_labels = ['domain_A', 'domain_B'] + (['replacement'] if case_id == 'F07' else [])
        cleanup_rows = cleanup.get('processes', [])
        cleanup_liveness = [row['payload'] for row in rows if row['event_id'] == 'liveness' and row['payload']['checkpoint'] == 'cleanup']
        if ([row['process'] for row in cleanup_rows] != expected_labels or not self.cohort._closed
                or len(cleanup_liveness) != len(expected_labels) or cleanup_liveness != cleanup.get('liveness')
                or any(row['poll_returncode'] is None or row['streams'] is None or
                       row['streams']['finished'] is not True or row['streams']['failure'] is not None or
                       row['streams']['eof'] != ['stderr', 'stdout'] for row in cleanup_rows)):
            errors.append('lcer.case_cleanup_incomplete')
        for row, sample in zip(cleanup_rows, cleanup_liveness):
            launch = self.cohort._entries[row['process']]['launch']
            if (sample['domain'] != launch['domain'] or sample['launch_id'] != launch['launch_id']
                    or sample['poll_returncode'] != row['poll_returncode'] or sample['observed_process'] is not None):
                errors.append('lcer.case_cleanup_incomplete')
        for row in cleanup_rows:
            if row['streams'] is not None:
                for stream in ('stdout', 'stderr'):
                    relative = case_id + '/' + row['process'] + '.' + stream + '.log'
                    if len(files[relative]) != row['streams']['stream_sizes'][stream]:
                        raise ValueError('lcer.case_artifact_changed')
        if time.monotonic() > self._deadline:
            errors.append('lcer.case_timeout')
        if not errors:
            if (set(bindings) != set(self.DOMAINS) or not self.canonical._core.canonical_coverage()['canonical_prefix_complete']
                    or (self.case['kind'] == 'witness' and (self._prefix != 5 or set(self._dispositions.values()) != {'current'}))
                    or (self.case['kind'] != 'witness' and (self._failure_code is None or self._terminal_capture is None))):
                raise ValueError('lcer.case_execution_incomplete')
        status = 'acquisition_failure' if errors else ('accepted' if self.case['kind'] == 'witness' else 'expected_failure')
        if not errors and self.case['kind'] != 'witness':
            errors = [self.case['failure_family']['failure_code'] if self.case['kind'] == 'failure' else self._failure_code]
        record = {'schema': 'city.live_evidence_case.v1', 'proof': 'Live Cross-Domain Evidence Round-Trip Proof', 'version': '0.1.0',
                  'witness_id': case_id, 'status': status, 'failure_codes': list(dict.fromkeys(errors)),
                  'process_bindings': [bindings[domain] for domain in self.DOMAINS if domain in bindings],
                  'liveness_checkpoints': [row['payload'] for row in rows if row['event_id'] == 'liveness'],
                  'canonical_artifacts': {'initial_raw_utf8': self._initial_raw.decode('utf-8'),
                                         'published_raw_utf8': self.canonical.head_raw.decode('utf-8') if self.canonical.publication_count else None,
                                         'terminal_raw_utf8': self.canonical.head_raw.decode('utf-8')},
                  'captured_evidence': captured, 'materialization_receipts': materializations, 'live_observations': observations,
                  'head_dispositions': [row['payload'] for row in rows if row['event_id'] == 'head_event'],
                  'command_trace': rows, 'artifact_sha256': hashes,
                  'claims': {'synchronized_representation': status == 'accepted', 'canonical_commit': self.canonical.publication_count == 1,
                             'production_ready': False, 'trusted_ci': False, 'game_sealed': False}}
        self.validator.validate('case_record', record)
        return record

    def execute_case(self):
        """Run one whole case, always clean up, then write its exclusive record.

        The outer acquisition still owes build/source authorization and native
        input binding. Public acquire remains closed until those gates exist.
        """
        if self._case_attempted or self._prefix != -1 or self._failed or self._running:
            raise ValueError('lcer.operation_sequence_invalid')
        self._case_attempted = True
        errors = []
        cleanup = {}
        try:
            self.run_prefix(self.case['prefix'])
            if self.case['kind'] != 'witness':
                self.run_failure()
                self.capture_terminal()
        except Exception as error:
            errors.append(str(error) or 'lcer.case_execution_failed')
        finally:
            try:
                cleanup = self.cohort.cleanup(60)
                errors.extend(row['code'] or 'lcer.case_cleanup_failed' for row in cleanup['errors'])
            finally:
                self.trace.close()
        self.workspace.verify()
        record = self._closed_case_record(errors, cleanup)
        raw = stored_json_bytes(record)
        path = self.workspace._output_root / self.case['id'] / 'record.json'
        self.cohort._budget.claim(len(raw))
        with path.open('xb') as stream:
            if stream.write(raw) != len(raw):
                raise OSError('lcer.case_record_write_failed')
            stream.flush()
            os.fsync(stream.fileno())
        if path.read_bytes() != raw:
            raise ValueError('lcer.case_record_write_invalid')
        self.workspace.verify()
        self._case_result = raw
        return parse_stored_json(raw)

    def run_prefix(self, prefix):
        if self.case != select_frozen_case(self._raw, self.cohort.case_id):
            raise ValueError('lcer.case_configuration_mismatch')
        allowed = 'P5' if self.case['kind'] == 'witness' else self.case['prefix']
        if (self._failed or self._running or prefix not in ('P0', 'P1', 'P2', 'P3', 'P4', 'P5')
                or int(prefix[1]) > int(allowed[1]) or int(prefix[1]) <= self._prefix):
            raise ValueError('lcer.operation_sequence_invalid')
        self._running = True
        try:
            while self._prefix < int(prefix[1]):
                self._timeout()
                self.workspace.verify()
                phase = self._prefix + 1
                if phase == 0:
                    self._head_event('initialize')
                    self.cohort.start_originals()
                    startups = self.cohort.read_startups(timeout=self._timeout())
                    project = external_file_identity(self.workspace._repository_root / self.world.policy['runtime']['project'])
                    for domain in self.DOMAINS:
                        row = self.cohort.sample(domain, 'startup')
                        if row['poll_returncode'] is not None or row['observed_process'] is None:
                            raise ValueError('lcer.original_process_exited')
                        self.world.startup(startups[domain])
                        connection = self.cohort.connection(domain)
                        launch = self.cohort.launch_record(domain)
                        binding = process_binding_from_observation(self._raw, connection.startup_raw, row['observed_process'],
                                                                   project, launch['process_root_realpath'], launch['environment']['USER'])
                        response = connection.bind(binding, timeout=self._timeout())['response']
                        if response['status'] != 'ok':
                            raise ValueError(response['error']['underlying_code'])
                        self._bindings[domain] = binding
                        self.canonical.retain_binding(binding)
                    for domain in self.DOMAINS:
                        self._materialize(domain, 'materialize_0001')
                    self._inspect('L0')
                elif phase == 1:
                    for domain in self.case.get('witness', {}).get('emission', self.DOMAINS):
                        self._emit(domain)
                    self._inspect('L1')
                elif phase == 2:
                    for _ in range(3):
                        self._canonical_call()
                    self._inspect('L2')
                elif phase == 3:
                    for domain in self.DOMAINS:
                        self._head_event('invalidate_claims', domain)
                    self._live('before_resolve')
                    self._canonical_call()
                    self._head_event('publish')
                    self._live('after_resolve')
                    for domain in self.DOMAINS:
                        self._head_event('classify', domain, 'stale')
                    self._inspect('L3')
                else:
                    domain = self.case.get('witness', {}).get('refresh', self.DOMAINS)[phase - 4]
                    self._materialize(domain, 'materialize_0002')
                    self._inspect('L' + str(phase))
                self._prefix = phase
        except BaseException:
            self._failed = True
            for domain in self.DOMAINS:
                self._dispositions[domain] = 'unclaimed'
            raise
        finally:
            self._running = False
        return {'completed_prefix': 'P' + str(self._prefix), 'publication_count': self.canonical.publication_count,
                'live_acceptance_verified': False}


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


class AcquisitionExecution:
    """Run the entire frozen acquisition once under its real prerequisites.

    A completed package still requires the separately invoked independent
    release verifier. Neither fixture execution nor byte-graph completion is
    live acceptance. The source audit gate remains mandatory on both paths.
    """

    def __init__(self, workspace, budget):
        if (not isinstance(workspace, AcquisitionWorkspace) or not isinstance(budget, CaptureBudget)
                or workspace._reserved or workspace._build_started or workspace._cases):
            raise ValueError('lcer.operation_sequence_invalid')
        self.workspace = workspace
        self.budget = budget
        self._attempted = False

    def execute(self):
        if self._attempted:
            raise ValueError('lcer.operation_sequence_invalid')
        self._attempted = True
        workspace = self.workspace
        workspace.verify()
        policy = FrozenObligationPlanCompiler(workspace._contract_raw).compile()['constitutional_policy']
        # This is the actual gate, not a supplied report or acceptance flag.
        # It currently rejects before even reserving acquisition directories.
        source_audit = workspace._require_build_source_audit()
        FrozenWireValidator(workspace._contract_raw).validate('source_audit', source_audit)
        if source_audit['returncode'] != 0:
            raise ValueError('lcer.source_audit_record_invalid')
        workspace.verify()
        workspace.reserve()
        writer = AcquisitionPackageWriter(workspace, self.budget)
        # Direct build independently enforces the same audit prerequisite.
        workspace.build_candidate()
        runtime_inputs = RuntimeBuildInputInventory.from_workspace(workspace)
        world = LiveWorldAcceptance.from_runtime_inputs(workspace._contract_raw, runtime_inputs)
        writer.write_references()
        launches = []
        for case_id in policy['artifact_hash_graph']['case_ids']:
            workspace.verify()
            runtime_inputs.verify()
            cohort = AcquisitionProcessCohort(workspace, case_id, runtime_inputs.cache,
                                               self.budget, runtime_inputs=runtime_inputs)
            try:
                record = CasePrefixExecution(cohort, world).execute_case()
            finally:
                # Also own failures between cohort creation and case entry,
                # including constructor failure and asynchronous interruption.
                try:
                    if not cohort._closed:
                        cohort.cleanup(60)
                finally:
                    cohort.trace.close()
            selected = select_frozen_case(workspace._contract_raw, case_id)
            expected_status = 'accepted' if selected['kind'] == 'witness' else 'expected_failure'
            if record['status'] != expected_status:
                raise ValueError('lcer.case_execution_failed')
            launches.extend({key: entry['launch'][key] for key in ('witness_id', 'domain', 'launch_id')}
                            for entry in cohort._entries.values())
        build = writer.observed_build_record(runtime_inputs, source_audit, launches)
        writer.write_build(build)
        return writer.finalize()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Frozen live evidence acquisition")
    routes = parser.add_subparsers(dest="command", required=True)
    acquire = routes.add_parser("acquire")
    acquire.add_argument("--runtime-parent", required=True)
    acquire.add_argument("--output", required=True)
    arguments = parser.parse_args(argv)
    raw = (PROOF_ROOT / 'live_cross_domain_evidence_round_trip_contract.json').read_bytes()
    workspace = AcquisitionWorkspace(raw, Path('/Users/boandersson/Projects/CITY'),
                                     arguments.runtime_parent, arguments.output)
    try:
        result = AcquisitionExecution(workspace, CaptureBudget(1024 * 1024 * 1024)).execute()
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
