"""Frozen implementation tests. Full live-release acceptance is outstanding."""

import sys

# unittest discovery adds this directory before importing the module. Close
# that path before loading further stdlib dependencies; the harness then
# validates the local source paths before its first model import.
_TEST_STDLIB = (getattr(sys, '_stdlib_dir', None) or sys.base_prefix +
                '/lib/python%d.%d' % sys.version_info[:2])
sys.path[:] = (_TEST_STDLIB, _TEST_STDLIB + '/lib-dynload',
               _TEST_STDLIB.rsplit('/', 1)[0] + '/python%d%d.zip' % sys.version_info[:2])
sys.dont_write_bytecode = True
sys.pycache_prefix = None

import copy
import argparse
import ctypes
import array
import base64
import hashlib
import json
import os
import select
import signal
import shutil
import socket
import stat
import struct
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock
import subprocess
import zlib

sys.path.insert(0, str(Path(__file__).absolute().parent))
from live_cross_domain_evidence_round_trip_harness import (
    AcquisitionExecution, AcquisitionPackageWriter, AcquisitionProcessCohort, AcquisitionWorkspace, CanonicalRoundTrip, CaptureBudget, CapturedCanonicalExecution, CasePrefixExecution, CoreRoundTripPipeline, LiveWorldAcceptance, MacProcessObserver, OriginalPipeMonitor, OriginalPipeProcess, OriginalProcessEvidence, OriginalProtocolConnection, RawTraceWriter,
    BuildActionInputInventory, RuntimeBuildInputInventory, UbtActionArchive, build_action_prerequisites, clang_dependency_paths, ubt_response_arguments,
    core_health, current_dyld_cache, current_dyld_process, current_python_runtime, dyld_cache_inventory, dyld_process_prefix, exact_pipe_holders, external_file_identity, frozen_launch_procargs, macho_file_images, parse_lsof_descriptors, process_binding_from_observation, python_runtime_from_build_log, reconcile_process_images, select_dyld_cache, vmmap_image_paths,
)
from live_cross_domain_evidence_round_trip import (
    FrozenObligationPlanCompiler,
    FrozenWireValidator,
    parse_stored_json,
    inspect_project_sources,
    source_file_bytes,
    select_frozen_case,
    stored_json_bytes,
    stdlib_top_level_names,
)


CONTRACT_PATH = Path(__file__).with_name("live_cross_domain_evidence_round_trip_contract.json")
_TEST_SOURCE_PREFLIGHT = inspect_project_sources(CONTRACT_PATH.read_bytes(), CONTRACT_PATH.parent.parent)
_TEST_CORE_HEALTH = core_health(CONTRACT_PATH.read_bytes(), CONTRACT_PATH.parent.parent)


class NormalUnittestBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='city-unittest-boundary-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        policy = json.loads(CONTRACT_PATH.read_bytes())
        names = (set(policy['planned_source_paths']) | set(policy['predecessors'])
                 | set(policy['unchanged_dependencies']) | set(policy['canonical_records'])
                 | {'proof_kernel/live_cross_domain_evidence_round_trip_contract.json',
                    'Live Cross-Domain Evidence Round-Trip Proof - Draft.md'})
        for name in names:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((CONTRACT_PATH.parent.parent / name).read_bytes())
        self.sentinel = self.root / 'unverified-source-executed'

    def invoke(self):
        return subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'proof_kernel',
                               '-p', 'test_live_cross_domain_evidence_round_trip.py'],
                              cwd=self.root, capture_output=True, timeout=15)

    def test_changed_immutable_module_blocks_discovery_before_its_body_runs(self):
        target = self.root / 'proof_kernel/concurrent_external_evidence_arbitration.py'
        target.write_bytes(('from pathlib import Path\nPath(%r).write_text("executed")\n' % str(self.sentinel)).encode())
        result = self.invoke()
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'lcer.dependency_identity_mismatch', result.stderr)
        self.assertIn(b'Failed to import test module', result.stderr)
        self.assertFalse(self.sentinel.exists())

    def test_stdlib_shadow_blocks_discovery_before_shadow_body_runs(self):
        target = self.root / 'proof_kernel/json.py'
        target.write_bytes(('from pathlib import Path\nPath(%r).write_text("executed")\n' % str(self.sentinel)).encode())
        result = self.invoke()
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'lcer.source_input_forbidden', result.stderr)
        self.assertFalse(self.sentinel.exists())


@unittest.skipUnless(sys.platform == "darwin", "Requires actual macOS process APIs")
class MacProcessObservationTests(unittest.TestCase):
    """Local interpreter processes exercise kernel reads, not Unreal runs."""

    def setUp(self):
        self.observer = MacProcessObserver()
        self.directory = tempfile.TemporaryDirectory(prefix="city-process-observer-", dir="/private/tmp")
        self.cwd = Path(self.directory.name).resolve()
        self.environment = {"HOME": str(self.cwd), "TMPDIR": str(self.cwd), "USER": "fixture",
                            "LOGNAME": "fixture", "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "C", "LC_ALL": "C"}
        parent_birth = self.observer.identity(os.getpid())["macos_birth_tuple"]
        # Use the observed interpreter binary. Python launcher stubs add their
        # own environment; protected /bin/cat omits environment from sysctl.
        self.binary = self.observer.paths(os.getpid(), parent_birth)["executable_realpath"]
        self.argv = [self.binary, "-B", "-c", 'import sys; print("ready", flush=True); sys.stdin.readline()']
        self.child = subprocess.Popen(self.argv, cwd=str(self.cwd), env=self.environment,
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(self.child.communicate, timeout=5)
        self.assertEqual(self.child.stdout.readline(), b"ready\n")
        self.identity = self.observer.identity(self.child.pid)
        self.birth = self.identity["macos_birth_tuple"]

    def test_kernel_process_identity_and_paths(self):
        self.assertEqual(self.identity["pid"], self.child.pid)
        self.assertEqual(self.identity["ppid"], os.getpid())
        self.assertGreater(self.birth["seconds"], 0)
        self.assertEqual(self.observer.paths(self.child.pid, self.birth),
                         {"cwd_realpath": str(self.cwd), "executable_realpath": self.binary})

    def test_current_loader_observation_matches_a_complete_installed_cache(self):
        observed = current_dyld_cache()
        process, cache = observed['process'], observed['inventory']
        self.assertGreaterEqual(process['all_image_info_size'], 200)
        self.assertEqual(process['all_image_info_format'], 1)
        self.assertEqual(process, current_dyld_process())
        self.assertEqual(cache['cache_uuids'][0].replace('-', ''), process['shared_cache_uuid'])
        self.assertIn(cache['main'], cache['files'])
        self.assertTrue(cache['images'])
        self.assertEqual(len({row['realpath'] for row in cache['images']}), len(cache['images']))
        self.assertTrue(all(row['sha256'] == cache['main']['sha256'] for row in cache['images']))

    def test_python_runtime_records_the_running_process_and_preserves_compiler_bytes(self):
        record = current_python_runtime()
        current = self.observer.identity(os.getpid())
        path = self.observer.paths(os.getpid(), current['macos_birth_tuple'])['executable_realpath']
        self.assertEqual(record['executable'], external_file_identity(path))
        self.assertEqual(record['version'], sys.version)
        self.assertEqual(record['version_info'], list(sys.version_info))
        raw = b'CITY_LCER_PYTHON ' + stored_json_bytes(record)
        compiler = b'actual-byte fixture\n\x00\xff\n'
        parsed, remainder = python_runtime_from_build_log(CONTRACT_PATH.read_bytes(), raw + compiler)
        self.assertEqual(parsed, record)
        self.assertEqual(remainder, compiler)

    def test_python_runtime_prelude_rejects_missing_duplicate_and_changed_shape(self):
        record = current_python_runtime()
        raw = b'CITY_LCER_PYTHON ' + stored_json_bytes(record)
        for changed in [b'', b'compiler output\n' + raw, raw + raw, raw.rstrip(b'\n')]:
            with self.assertRaisesRegex(ValueError, '^lcer.python_runtime_log_invalid$'):
                python_runtime_from_build_log(CONTRACT_PATH.read_bytes(), changed)
        for key, value in [('extra', True), ('schema', 'unlisted'), ('version', ''),
                           ('version_info', [3, 14, True, 'final', 0])]:
            changed = {**record, key: value}
            with self.assertRaisesRegex(ValueError, '^lcer.python_runtime_log_invalid$'):
                python_runtime_from_build_log(CONTRACT_PATH.read_bytes(), b'CITY_LCER_PYTHON ' + stored_json_bytes(changed))

    def test_running_child_without_observed_exec_boundary_rejects(self):
        with self.assertRaisesRegex(ValueError, '^lcer.launch_boundary_unobserved$'):
            self.observer.launch_inputs(self.child.pid, self.birth)

    def test_launch_inputs_are_reread_after_bootstrap_strings_are_consumed(self):
        process = OriginalPipeProcess(self.observer)
        self.addCleanup(self._close_spawned, process)
        process.start(self.argv, self.environment, self.cwd)
        process.resume()
        self.assertTrue(select.select([process.stdout_fd], [], [], 5)[0])
        self.assertEqual(os.read(process.stdout_fd, 64), b'ready\n')
        self.assertEqual(self.observer.launch_inputs(process.pid, process.birth), (self.argv, self.environment))
        self.assertEqual(self.observer.launch_inputs(process.pid, process.birth), (self.argv, self.environment))

    def test_changed_initial_environment_bytes_reject_a_later_sample(self):
        program = ('import ctypes,sys; libc=ctypes.CDLL("/usr/lib/libSystem.B.dylib"); '
                   'libc.getenv.argtypes=[ctypes.c_char_p]; libc.getenv.restype=ctypes.c_void_p; '
                   'ctypes.memmove(libc.getenv(b"USER"), b"x", 1); '
                   'print("changed",flush=True); sys.stdin.readline()')
        process = OriginalPipeProcess(self.observer)
        self.addCleanup(self._close_spawned, process)
        process.start([self.binary, '-B', '-c', program], self.environment, self.cwd)
        process.resume()
        self.assertTrue(select.select([process.stdout_fd], [], [], 5)[0])
        self.assertEqual(os.read(process.stdout_fd, 64), b'changed\n')
        with self.assertRaisesRegex(ValueError, '^lcer.process_input_invalid$'):
            self.observer.launch_inputs(process.pid, process.birth)

    def test_actual_suspended_environment_covers_every_string_alignment(self):
        for length in range(8):
            with self.subTest(comment_length=length):
                argv = [self.binary, '-B', '-c', 'pass #' + 'x' * length]
                process = OriginalPipeProcess(self.observer)
                self.addCleanup(self._close_spawned, process)
                try:
                    process.start(argv, self.environment, self.cwd)
                    self.assertEqual(self.observer.launch_inputs(process.pid, process.birth),
                                     (argv, self.environment))
                finally:
                    self._close_spawned(process)

    def test_actual_bootstrap_named_extra_environment_is_rejected(self):
        for key in ('pfz', 'dyld_hw_tpro', 'dyld_hw_tpro_pagers'):
            with self.subTest(key=key):
                process = OriginalPipeProcess(self.observer)
                self.addCleanup(self._close_spawned, process)
                try:
                    with self.assertRaisesRegex(ValueError, '^lcer.process_environment_invalid$'):
                        process.start(self.argv, {**self.environment, key: '1'}, self.cwd)
                    self.assertIsNotNone(process.pid)
                finally:
                    self._close_spawned(process)

    def test_original_three_pipes_match_parent_kernel_peers(self):
        self.assertEqual(self.observer.descriptor_list(self.child.pid, self.birth), [(0, 6), (1, 6), (2, 6)])
        parent_birth = self.observer.identity(os.getpid())["macos_birth_tuple"]
        for fd, stream in enumerate((self.child.stdin, self.child.stdout, self.child.stderr)):
            child = self.observer.pipe(self.child.pid, self.birth, fd)
            parent = self.observer.pipe(os.getpid(), parent_birth, stream.fileno())
            self.assertEqual(child["kernel_id"], parent["peer_kernel_id"])
            self.assertEqual(child["peer_kernel_id"], parent["kernel_id"])
            self.assertEqual(child["access"], "read" if fd == 0 else "write")
            self.assertEqual(parent["access"], "write" if fd == 0 else "read")

    def test_closed_peer_is_observed_as_null_while_original_endpoint_remains(self):
        reader, writer = os.pipe()
        self.addCleanup(os.close, reader)
        birth = self.observer.identity(os.getpid())['macos_birth_tuple']
        before = self.observer.pipe(os.getpid(), birth, reader)
        os.close(writer)
        after = self.observer.pipe(os.getpid(), birth, reader)
        self.assertEqual(after, {**before, 'peer_kernel_id': None})
        result = subprocess.run(['/usr/sbin/lsof', '-nP', '-a', '-p', str(os.getpid()),
                                 '-d', str(reader), '-F0pftnd'], capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = parse_lsof_descriptors(result.stdout, os.getpid())
        self.assertEqual(rows, [{'fd': reader, 'type': 'PIPE',
                                'device': '0x' + after['kernel_id'].lstrip('0'), 'name': ''}])

    def test_changed_birth_rejects_before_sensitive_process_reads(self):
        changed = {**self.birth, "seconds": self.birth["seconds"] + 1}
        for function, extra in [(self.observer.paths, []), (self.observer.launch_inputs, []),
                                (self.observer.descriptor_list, []), (self.observer.pipe, [0])]:
            with self.subTest(function=function.__name__):
                with self.assertRaisesRegex(ValueError, "^lcer.process_identity_mismatch$"):
                    function(self.child.pid, changed, *extra)

    def test_lsof_independently_matches_all_original_pipe_handles(self):
        rows = self.observer.checked_descriptors(self.child.pid, self.birth)
        self.assertEqual(rows, [self.observer.pipe(self.child.pid, self.birth, fd) for fd in range(3)])

    def test_pipe_census_records_visible_holders_and_retains_visibility_gaps(self):
        parent_birth = self.observer.identity(os.getpid())['macos_birth_tuple']
        expected = [self.observer.pipe(self.child.pid, self.birth, fd) for fd in range(3)]
        expected.extend(self.observer.pipe(os.getpid(), parent_birth, stream.fileno())
                        for stream in (self.child.stdin, self.child.stdout, self.child.stderr))
        census = self.observer.pipe_holder_census(expected)
        self.assertIn(os.getpid(), census['enumerated_pids'])
        self.assertIn(self.child.pid, census['enumerated_pids'])
        self.assertEqual(exact_pipe_holders(expected, census['holders']),
                         sorted(expected, key=lambda row: (row['pid'], row['fd'])))
        self.assertIs(self.observer.last_pipe_census, census)
        # This proves visible endpoint matching only. The public acceptance
        # route separately rejects every retained visibility gap.

    def _original_endpoints(self):
        parent_birth = self.observer.identity(os.getpid())['macos_birth_tuple']
        rows = [self.observer.pipe(self.child.pid, self.birth, fd) for fd in range(3)]
        rows.extend(self.observer.pipe(os.getpid(), parent_birth, stream.fileno())
                    for stream in (self.child.stdin, self.child.stdout, self.child.stderr))
        return rows, {os.getpid(): parent_birth, self.child.pid: self.birth}

    def test_unique_original_holders_use_kernel_sharing_and_lsof(self):
        rows, births = self._original_endpoints()
        self.assertEqual(self.observer.exclusive_pipe_holders(rows, births),
                         sorted(rows, key=lambda row: (row['pid'], row['fd'])))
        self.assertEqual(len(self.observer.last_pipe_exclusivity), 12)
        self.assertTrue(all(row['fi_status'] & 1 == 0 for row in self.observer.last_pipe_exclusivity))
        self.assertIsNone(self.observer.last_pipe_census)

    def test_duplicate_original_endpoint_rejects_even_in_same_process(self):
        rows, births = self._original_endpoints()
        duplicate = os.dup(self.child.stdout.fileno())
        try:
            with self.assertRaisesRegex(ValueError, '^lcer.proof_pipe_extra_holder$'):
                self.observer.exclusive_pipe_holders(rows, births)
        finally:
            os.close(duplicate)
        self.assertEqual(len(self.observer.exclusive_pipe_holders(rows, births)), 6)

    def test_offline_helper_retaining_an_original_pipe_rejects(self):
        rows, births = self._original_endpoints()
        helper = subprocess.Popen([self.binary, '-I', '-B', '-c',
                                   'import sys; print("ready",flush=True); sys.stdin.readline()'],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  close_fds=True, pass_fds=(self.child.stdout.fileno(),))
        try:
            self.assertTrue(select.select([helper.stdout], [], [], 5)[0])
            self.assertEqual(helper.stdout.readline(), b'ready\n')
            with self.assertRaisesRegex(ValueError, '^lcer.proof_pipe_extra_holder$'):
                self.observer.exclusive_pipe_holders(rows, births)
        finally:
            helper.communicate(timeout=5)
        self.assertEqual(helper.returncode, 0)

    def test_queued_descriptor_transfer_rejects_before_another_fd_exists(self):
        rows, births = self._original_endpoints()
        left, right = socket.socketpair()
        try:
            self.assertEqual(left.sendmsg([b'x'], [(socket.SOL_SOCKET, socket.SCM_RIGHTS,
                                                   array.array('i', [self.child.stdout.fileno()]))]), 1)
            with self.assertRaisesRegex(ValueError, '^lcer.proof_pipe_extra_holder$'):
                self.observer.exclusive_pipe_holders(rows, births)
        finally:
            left.close()
            right.close()

    def test_missing_peer_cannot_be_excluded_from_holder_observation(self):
        rows, births = self._original_endpoints()
        with self.assertRaisesRegex(ValueError, '^lcer.original_pipe_identity_mismatch$'):
            self.observer.exclusive_pipe_holders(rows[1:], births)
        changed = copy.deepcopy(rows)
        changed[0]['peer_kernel_id'] = None
        with self.assertRaisesRegex(ValueError, '^lcer.original_pipe_identity_mismatch$'):
            self.observer.exclusive_pipe_holders(changed, births)

    def test_unique_holder_check_rejects_a_changed_birth(self):
        rows, births = self._original_endpoints()
        births[self.child.pid] = {**self.birth, 'seconds': self.birth['seconds'] + 1}
        with self.assertRaisesRegex(ValueError, '^lcer.process_identity_mismatch$'):
            self.observer.exclusive_pipe_holders(rows, births)

    def test_unmatched_retained_peer_after_original_close_rejects(self):
        reader, writer = os.pipe()
        try:
            parent_birth = self.observer.identity(os.getpid())['macos_birth_tuple']
            row = self.observer.pipe(os.getpid(), parent_birth, reader)
            with self.assertRaisesRegex(ValueError, '^lcer.proof_pipe_extra_holder$'):
                self.observer.exclusive_pipe_holders([{**row, 'peer_kernel_id': None}],
                                                    {os.getpid(): parent_birth})
        finally:
            os.close(reader)
            os.close(writer)

    def test_original_process_retains_unique_endpoints_through_exit(self):
        process = OriginalPipeProcess(self.observer)
        self.addCleanup(self._close_spawned, process)
        process.start(self.argv, self.environment, self.cwd)
        before = process.observe_original_holders()
        self.assertIsNone(before['poll_returncode'])
        self.assertEqual(len(before['pipe_holders']), 6)
        process.send_signal(signal.SIGKILL)
        process.wait(5)
        after = process.observe_original_holders()
        self.assertEqual(after['poll_returncode'], -signal.SIGKILL)
        self.assertEqual(len(after['pipe_holders']), 3)
        self.assertTrue(all(row['peer_kernel_id'] is None for row in after['pipe_holders']))
        duplicate = os.dup(process.stdout_fd)
        try:
            with self.assertRaisesRegex(ValueError, '^lcer.proof_pipe_extra_holder$'):
                process.observe_original_holders()
        finally:
            os.close(duplicate)
        process.close_pipes()
        with self.assertRaisesRegex(ValueError, '^lcer.original_pipe_identity_mismatch$'):
            process.observe_original_holders()

    def test_macho_uuid_and_architecture_match_apple_dwarfdump(self):
        rows = macho_file_images(self.binary)
        result = subprocess.run(['/usr/bin/dwarfdump', '--uuid', self.binary], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = sorted((line.split()[1].lower(), line.split()[2].strip('()'))
                          for line in result.stdout.splitlines() if line.startswith('UUID: '))
        self.assertTrue(expected)
        self.assertIn(self.observer.architecture(self.child.pid, self.birth), [row['architecture'] for row in rows])
        self.assertEqual(sorted((row['macho_uuid'], row['architecture']) for row in rows), expected)

    def _close_spawned(self, process):
        try:
            if process.pid is not None and process.poll() is None:
                process.send_signal(signal.SIGKILL)
                process.wait(5)
        finally:
            process.close_pipes()

    def test_suspended_exec_has_only_three_original_descriptors(self):
        with (self.cwd / 'must-not-inherit.txt').open('wb') as extra:
            os.set_inheritable(extra.fileno(), True)
            process = OriginalPipeProcess(self.observer)
            self.addCleanup(self._close_spawned, process)
            process.start(self.argv, self.environment, self.cwd)
            self.assertEqual([r['fd'] for r in process.exec_descriptors], [0, 1, 2])
            self.assertIsNone(process.poll())
            self.assertEqual(select.select([process.stdout_fd], [], [], 0)[0], [])
            process.resume()
            self.assertEqual(select.select([process.stdout_fd], [], [], 5)[0], [process.stdout_fd])
            self.assertEqual(os.read(process.stdout_fd, 64), b'ready\n')
            with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
                process.resume()
            os.write(process.stdin_fd, b'finish\n')
            self.assertEqual(process.wait(5), 0)

    def _monitored_process(self, program):
        process = OriginalPipeProcess(self.observer)
        # A suspended child belongs to this test even when start validation
        # fails before the monitor exists. Register cleanup before spawning.
        self.addCleanup(self._close_spawned, process)
        try:
            process.start([self.binary, '-B', '-c', program], self.environment, self.cwd)
        except ValueError as error:
            raise AssertionError(str(error) + ': ' + json.dumps(process.launch_validation, sort_keys=True)) from error
        stdout = self.cwd / 'captured.stdout'
        stderr = self.cwd / 'captured.stderr'
        monitor = OriginalPipeMonitor(process, stdout, stderr, CaptureBudget(1024 * 1024))
        def cleanup():
            try:
                if process.poll() is None:
                    process.send_signal(signal.SIGKILL)
                    process.wait(5)
                try:
                    monitor.finish(5)
                except ValueError:
                    pass  # Tests retain and assert deliberate transport failure.
            finally:
                process.close_pipes()
        self.addCleanup(cleanup)
        monitor.start()
        process.resume()
        return process, monitor, stdout, stderr

    def test_failed_suspended_launch_is_still_owned_and_reaped_by_test_cleanup(self):
        original = self.observer.launch_inputs
        seen = []
        def wrong_inputs(pid, birth):
            argv, environment = original(pid, birth)
            seen.append(pid)
            return argv, {**environment, 'EXTRA_FIXTURE_KEY': 'denied'}
        self.observer.launch_inputs = wrong_inputs
        try:
            with self.assertRaisesRegex(AssertionError, '^lcer.process_input_invalid:'):
                self._monitored_process('import sys; sys.stdin.readline()')
        finally:
            self.observer.launch_inputs = original
        self.assertEqual(len(seen), 1)
        self.assertEqual(self.observer.identity(seen[0])['ppid'], os.getpid())
        self.doCleanups()
        with self.assertRaises(ChildProcessError):
            os.waitpid(seen[0], os.WNOHANG)

    def test_continuous_capture_drains_stderr_and_preserves_split_protocol_offsets(self):
        program = ('import os,sys,time; '
                   'os.write(1,b"ordinary log\\n"+b"{\\"ready\\":true}\\n"[:5]); '
                   'time.sleep(0.05); os.write(2,b"s"*262144); '
                   'os.write(1,b"{\\"ready\\":true}\\n"[5:]); '
                   'line=sys.stdin.buffer.readline(); os.write(1,line); os.write(2,b"\\xfflast")')
        process, monitor, stdout, stderr = self._monitored_process(program)
        time.sleep(0.1)  # The parent does other work while both pipes drain.
        ready = b'{"ready":true}\n'
        self.assertEqual(monitor.next_protocol_line(5), (len(b'ordinary log\n'), ready))
        command = stored_json_bytes({'command': 'fixture'})
        self.assertEqual(monitor.send(command, 5), 0)
        self.assertEqual(monitor.next_protocol_line(5), (len(b'ordinary log\n') + len(ready), command))
        self.assertEqual(process.wait(5), 0)
        final = monitor.finish(5)
        self.assertEqual(final['eof'], ['stderr', 'stdout'])
        self.assertEqual(final['poll_returncode'], 0)
        self.assertEqual(stdout.read_bytes(), b'ordinary log\n' + ready + command)
        self.assertEqual(stderr.read_bytes(), b's' * 262144 + b'\xfflast')
        self.assertEqual(monitor.stdin_bytes(), command)
        self.assertEqual(final['stream_sizes'], {'stdout': stdout.stat().st_size, 'stderr': stderr.stat().st_size})

    def test_stdout_eof_does_not_fabricate_process_exit(self):
        process, monitor, stdout, stderr = self._monitored_process('import os,sys; os.close(1); sys.stdin.readline()')
        with self.assertRaisesRegex(EOFError, '^lcer.original_stdout_eof$'):
            monitor.next_protocol_line(5)
        self.assertIsNone(process.poll())
        state = monitor.observation()
        self.assertEqual(state['eof'], ['stdout'])
        self.assertIsNone(state['poll_returncode'])
        self.assertEqual(stdout.read_bytes(), b'')

    def test_original_streams_keep_draining_while_process_identity_is_locked(self):
        program = ('import os,sys; sys.stdin.readline(); '
                   'os.write(2,b"s"*262144); os.write(1,b"x"*262144+b"\\n"); '
                   'os.write(1,b"{\\"ready\\":true}\\n")')
        process, monitor, stdout, stderr = self._monitored_process(program)
        with process._wait_lock:
            # A fixture trigger models a child logging during a long parent
            # observation. It is not a live protocol command or acceptance.
            os.write(process.stdin_fd, b'{}\n')
            self.assertEqual(monitor.next_protocol_line(5), (262145, b'{"ready":true}\n'))
            self.assertEqual(stdout.read_bytes(), b'x' * 262144 + b'\n{"ready":true}\n')
            self.assertEqual(stderr.read_bytes(), b's' * 262144)
        self.assertEqual(process.wait(5), 0)
        self.assertEqual(monitor.finish(5)['eof'], ['stderr', 'stdout'])

    def test_truncated_protocol_is_retained_and_cannot_pass_drain(self):
        process, monitor, stdout, stderr = self._monitored_process('import os; os.write(1,b"{broken")')
        with self.assertRaisesRegex(ValueError, '^lcer.protocol_line_truncated$'):
            monitor.next_protocol_line(5)
        self.assertEqual(process.wait(5), 0)
        with self.assertRaisesRegex(ValueError, '^lcer.protocol_line_truncated$'):
            monitor.finish(5)
        self.assertEqual(stdout.read_bytes(), b'{broken')

    def test_signal_rejects_a_changed_birth_without_terminating_child(self):
        process = OriginalPipeProcess(self.observer)
        self.addCleanup(self._close_spawned, process)
        process.start(self.argv, self.environment, self.cwd)
        birth = process.birth
        process.birth = {**birth, 'seconds': birth['seconds'] + 1}
        try:
            with self.assertRaisesRegex(ValueError, '^lcer.process_identity_mismatch$'):
                process.send_signal(signal.SIGKILL)
        finally:
            process.birth = birth
        self.assertIsNone(process.poll())

    def _process_evidence(self):
        # Only the mapped-image boundary is a fixture. PID/birth, launch
        # strings, executable, cwd, fd records, lsof and original pipes are
        # observed from an actual disposable Python child. No game claim.
        image = self.cwd / 'image-fixture.dylib'
        image.write_bytes(struct.pack('<IiiIIIII', 0xfeedfacf, 0x0100000c, 0, 6, 1, 24, 0, 0)
                          + struct.pack('<II', 0x1b, 24) + bytes(range(16)))
        image_row, = macho_file_images(image)
        startup = {'schema': 'city.live_evidence_startup.v1', 'witness_id': 'W1',
                   'domain': 'domain_A', 'launch_id': 'fixture_launch', 'pid': 0,
                   'cwd_realpath': str(self.cwd), 'worlds': [], 'controllers': [],
                   'loaded_images': [image_row], 'enabled_plugins': [], 'config_files': [],
                   'proof_module': image_row}
        opened = self.cwd / 'open-input.bin'
        opened.write_bytes(b'initial')
        program = ('import os,json,sys; '
                   'retained=open(%r,"rb"); startup=%r; startup["pid"]=os.getpid(); '
                   'print(json.dumps(startup,sort_keys=True,separators=(",",":")),flush=True); '
                   'sys.stdin.readline()') % (str(opened), startup)
        process, monitor, _, _ = self._monitored_process(program)
        trace = RawTraceWriter(CONTRACT_PATH.read_bytes(), self.cwd / 'process-trace.jsonl')
        self.addCleanup(trace.close)
        connection = OriginalProtocolConnection(CONTRACT_PATH.read_bytes(), 'W1', 'domain_A',
                                                'fixture_launch', monitor, trace)
        connection.read_startup(5)
        original = self.observer.image_mappings
        self.observer.image_mappings = lambda pid, birth: [str(image)]
        self.addCleanup(setattr, self.observer, 'image_mappings', original)
        evidence = OriginalProcessEvidence(CONTRACT_PATH.read_bytes(), connection,
                                           {'main': {'sha256': '0' * 64}, 'images': []})
        return evidence, opened, image

    def test_runtime_build_mismatch_blocks_actual_process_observation_before_trace_acceptance(self):
        fixture = RuntimeBuildInputInventoryTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        original, _, _ = self._process_evidence()
        evidence = OriginalProcessEvidence(CONTRACT_PATH.read_bytes(), original.connection,
                                           fixture.inventory.cache, runtime_inputs=fixture.inventory)
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_build_identity_mismatch$'):
            evidence.sample('startup')
        self.assertIsNone(evidence.process.poll())
        self.assertFalse(any(row['event_id'] in ('process_observation', 'liveness')
                             for row in evidence.connection.trace.rows()))

    def test_process_evidence_samples_current_kernel_files_and_original_endpoints(self):
        evidence, opened, _ = self._process_evidence()
        first = evidence.sample('startup')
        self.assertIsNone(first['poll_returncode'])
        record = first['observed_process']
        self.assertEqual(record['pid'], evidence.process.pid)
        self.assertEqual(record['ppid'], os.getpid())
        self.assertEqual(record['macos_birth_tuple'], evidence.process.birth)
        self.assertEqual(record['environment'], self.environment)
        self.assertEqual(record['executable'], external_file_identity(self.binary))
        self.assertEqual(record['open_files'], [external_file_identity(opened)])
        self.assertEqual(len(first['pipe_endpoints']), 6)
        self.assertEqual(first['pipe_endpoints'], first['pipe_holders'])
        opened.write_bytes(b'changed after the first sample')
        second = evidence.sample('L0')
        self.assertEqual(second['observed_process']['open_files'], [external_file_identity(opened)])
        self.assertNotEqual(first['observed_process']['open_files'], second['observed_process']['open_files'])
        rows = evidence.connection.trace.rows()
        self.assertEqual([row['event_id'] for row in rows],
                         ['wire_event', 'process_observation', 'liveness', 'process_observation', 'liveness'])
        self.assertEqual(rows[-1]['payload'], second)
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            evidence.sample('L0')

    def test_fault_snapshot_observes_real_exit_without_consuming_terminal_checkpoint(self):
        evidence, opened, _ = self._process_evidence()
        initial_trace = evidence.connection.trace.rows()
        before = evidence.snapshot('terminal')
        opened.write_bytes(b'changed before the fault action')
        fresh = evidence.snapshot('terminal')
        self.assertNotEqual(before['observed_process']['open_files'], fresh['observed_process']['open_files'])
        self.assertEqual(evidence.connection.trace.rows(), initial_trace)
        self.assertTrue(evidence.process.send_signal(signal.SIGTERM))
        self.assertEqual(evidence.process.wait(5), -int(signal.SIGTERM))
        after = evidence.snapshot('terminal')
        self.assertEqual(after['poll_returncode'], -int(signal.SIGTERM))
        self.assertIsNone(after['observed_process'])
        self.assertEqual(len(after['pipe_endpoints']), 3)
        self.assertEqual(after['pipe_endpoints'], after['pipe_holders'])
        self.assertEqual(evidence.connection.trace.rows(), initial_trace)
        terminal = evidence.sample('terminal')
        self.assertEqual(terminal, after)
        self.assertEqual(evidence.connection.trace.rows()[-1]['payload'], terminal)

    def test_process_evidence_rejects_changed_launch_strings_without_reusing_receipt(self):
        evidence, _, _ = self._process_evidence()
        evidence.sample('startup')
        original = self.observer.launch_inputs
        def changed(pid, birth):
            argv, environment = original(pid, birth)
            return argv, {**environment, 'USER': 'changed'}
        self.observer.launch_inputs = changed
        try:
            with self.assertRaisesRegex(ValueError, '^lcer.process_input_invalid$'):
                evidence.sample('L0')
        finally:
            self.observer.launch_inputs = original
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            evidence.sample('L1')
        self.assertEqual([row['payload']['checkpoint'] for row in evidence.connection.trace.rows()
                          if row['event_id'] == 'liveness'], ['startup'])

    def test_process_evidence_rejects_replaced_startup_or_changed_mapped_image(self):
        evidence, _, image = self._process_evidence()
        evidence.sample('startup')
        original = evidence.connection.startup_raw
        changed = parse_stored_json(original)
        changed['pid'] += 1
        evidence.connection.startup_raw = stored_json_bytes(changed)
        try:
            with self.assertRaisesRegex(ValueError, '^lcer.protocol_identity_mismatch$'):
                evidence.sample('L0')
        finally:
            evidence.connection.startup_raw = original
        # Terminal evidence is still attempted after failure. A changed image
        # must fail its fresh byte/UUID check, rather than reuse startup data.
        raw = bytearray(image.read_bytes()); raw[-1] ^= 1; image.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, '^lcer.process_images_invalid$'):
            evidence.sample('terminal')

    def test_process_evidence_death_requires_original_wait_and_unique_retained_pipes(self):
        evidence, _, _ = self._process_evidence()
        evidence.sample('startup')
        evidence.process.send_signal(signal.SIGKILL)
        self.assertEqual(evidence.process.wait(5), -signal.SIGKILL)
        after = evidence.sample('terminal')
        self.assertEqual(after['poll_returncode'], -signal.SIGKILL)
        self.assertIsNone(after['observed_process'])
        self.assertEqual(len(after['pipe_holders']), 3)
        self.assertTrue(all(row['peer_kernel_id'] is None for row in after['pipe_holders']))
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            evidence.sample('L1')
        duplicate = os.dup(evidence.process.stdout_fd)
        try:
            with self.assertRaisesRegex(ValueError, '^lcer.proof_pipe_extra_holder$'):
                evidence.sample('cleanup')
        finally:
            os.close(duplicate)

    def test_independent_liveness_checks_actual_child_samples_and_exit(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        policy = json.loads(CONTRACT_PATH.read_bytes())
        evidence, opened, _ = self._process_evidence()
        samples = [evidence.sample('startup')]
        opened.write_bytes(b'actual dynamic open-file change')
        samples.append(evidence.sample('L0'))
        evidence.process.send_signal(signal.SIGTERM)
        self.assertEqual(evidence.process.wait(5), -int(signal.SIGTERM))
        samples.append(evidence.sample('terminal'))
        samples.append(evidence.sample('cleanup'))
        self.assertEqual(verifier._liveness_series_relations(policy, samples), samples)
        changed = copy.deepcopy(samples)
        changed[-1]['pipe_holders'].append(dict(changed[-1]['pipe_holders'][0], fd=99999))
        with self.assertRaisesRegex(ValueError, '^lcer.proof_pipe_extra_holder$'):
            verifier._liveness_series_relations(policy, changed)

    def test_process_evidence_rejects_replaced_original_identity(self):
        evidence, _, _ = self._process_evidence()
        original = evidence.process.birth
        evidence.process.birth = {**original, 'seconds': original['seconds'] + 1}
        try:
            with self.assertRaisesRegex(ValueError, '^lcer.original_process_identity_mismatch$'):
                evidence.sample('startup')
        finally:
            evidence.process.birth = original
        self.assertIsNone(evidence.process.poll())

    def test_process_evidence_rejects_a_file_changed_during_observation(self):
        evidence, opened, _ = self._process_evidence()
        mappings = self.observer.image_mappings
        def change_after_file_read(pid, birth):
            opened.write_bytes(b'changed after descriptor hashing')
            return mappings(pid, birth)
        self.observer.image_mappings = change_after_file_read
        try:
            with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
                evidence.sample('startup')
        finally:
            self.observer.image_mappings = mappings
        self.assertEqual([row['event_id'] for row in evidence.connection.trace.rows()], ['wire_event'])


class ProcessByteParserTests(unittest.TestCase):
    def _dyld_prefix_fixture(self):
        raw = bytearray(200)
        struct.pack_into('<II', raw, 0, 17, 12)
        raw[25] = 1
        struct.pack_into('<Q', raw, 104, 0x1000)
        raw[160:176] = bytes(range(1, 17))
        struct.pack_into('<QQ', raw, 176, 0x200000000, 123)
        return bytes(raw)

    def test_dyld_prefix_requires_attached_initialized_versioned_self_pointer(self):
        raw = self._dyld_prefix_fixture()
        result = dyld_process_prefix(raw, 0x1000)
        self.assertEqual(result['shared_cache_uuid'], bytes(range(1, 17)).hex())
        self.assertEqual(result['prefix_sha256'], hashlib.sha256(raw).hexdigest())
        changes = [(0, struct.pack('<I', 14)), (4, bytes(4)), (24, b'\x01'), (24, b'\x02'),
                   (25, b'\x00'), (104, struct.pack('<Q', 0x2000)), (160, bytes(16)),
                   (176, bytes(8)), (184, bytes(8))]
        for offset, replacement in changes:
            changed = bytearray(raw); changed[offset:offset + len(replacement)] = replacement
            with self.assertRaisesRegex(ValueError, '^lcer.dyld_process_observation_invalid$'):
                dyld_process_prefix(bytes(changed), 0x1000)
        for changed, address in ((raw[:-1], 0x1000), (raw + b'\0', 0x1000), (raw, 0x1001), (raw, True)):
            with self.assertRaisesRegex(ValueError, '^lcer.dyld_process_observation_invalid$'):
                dyld_process_prefix(changed, address)

    def test_cache_selection_uses_uuid_and_deduplicates_realpath_aliases(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            main = self._cache_fixture(directory)
            alias = Path(directory) / 'cache-alias'
            alias.symlink_to(main)
            selected = select_dyld_cache(bytes(range(1, 17)).hex(), [main, alias, Path(directory) / 'missing'])
            self.assertEqual(selected, external_file_identity(main))

    def test_cache_selection_rejects_missing_or_distinct_ambiguous_matches(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            main = self._cache_fixture(directory)
            other = Path(directory) / 'duplicate-cache'
            other.write_bytes(main.read_bytes())
            for uuid, paths in [('f' * 32, [main]), (bytes(range(1, 17)).hex(), [main, other]),
                                ('0' * 32, [main]), ('invalid', [main]), (bytes(range(1, 17)).hex(), ['relative'])]:
                with self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_selection_invalid$'):
                    select_dyld_cache(uuid, paths)

    def test_cache_selection_rechecks_header_after_hashing(self):
        from unittest import mock
        import live_cross_domain_evidence_round_trip_harness as harness
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            main = self._cache_fixture(directory)
            identity = harness.external_file_identity
            def changed(path):
                raw = bytearray(main.read_bytes()); raw[88] ^= 1; main.write_bytes(raw)
                return identity(path)
            with mock.patch.object(harness, 'external_file_identity', side_effect=changed):
                with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
                    select_dyld_cache(bytes(range(1, 17)).hex(), [main])

    def test_cache_discovery_rejects_a_changed_loader_observation(self):
        from unittest import mock
        import live_cross_domain_evidence_round_trip_harness as harness
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            cache = dyld_cache_inventory(self._cache_fixture(directory))
            before = dyld_process_prefix(self._dyld_prefix_fixture(), 0x1000)
            after = {**before, 'info_array_change_timestamp': 124}
            with mock.patch.object(harness, 'current_dyld_process', side_effect=[before, after]), \
                    mock.patch.object(harness, 'select_dyld_cache', return_value=cache['main']), \
                    mock.patch.object(harness, 'dyld_cache_inventory', return_value=cache):
                with self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_observation_changed$'):
                    current_dyld_cache()

    def _procargs_fixture(self, length=0, environment=None, tail=(), prefix=()):
        argv = ['/fixture/python', '-c', 'pass #' + 'x' * length]
        if environment is None:
            environment = [('HOME', '/fixture'), ('TMPDIR', '/fixture'), ('USER', 'fixture'),
                           ('LOGNAME', 'fixture'), ('PATH', '/usr/bin'), ('LANG', 'C'), ('LC_ALL', 'C')]
        body = b'/fixture/python\0' + b'\0'.join(arg.encode() for arg in argv) + b'\0'
        body += b''.join((key + '=' + value).encode() + b'\0' for key, value in environment)
        body += bytes(-len(body) % 8)
        suffix = [b'pfz=0x1', b'stack_guard=0x2', b'malloc_entropy=0x3,0x4', b'ptr_munge=0x5',
                  b'main_stack=0x6,0x7,0x8,0x9', b'executable_file=0xa,0xb', b'dyld_file=0xc,0xd',
                  b'executable_cdhash=' + b'1' * 40, b'executable_boothash=' + b'2' * 40,
                  b'arm64e_abi=os', b'th_port=0xe', b'security_config=0x0']
        body += b'\0'.join([*prefix, *suffix, *tail]) + b'\0'
        body += bytes(-len(body) % 8)
        return struct.pack('=i', len(argv)) + body, argv, dict(environment)

    def test_procargs_requires_complete_suffix_at_every_alignment(self):
        for length in range(8):
            for tail in ((), (b'dyld_hw_tpro=1',), (b'dyld_hw_tpro=1', b'dyld_hw_tpro_pagers=1')):
                with self.subTest(length=length, tail=tail):
                    raw, argv, environment = self._procargs_fixture(length, tail=tail)
                    self.assertEqual(frozen_launch_procargs(raw), (argv, environment))
                    # A complete forged suffix before the real kernel block
                    # cannot hide extra environment strings.
                    marker = raw.index(b'pfz=')
                    spoofed = raw[:marker] + raw[marker:] + raw[marker:]
                    with self.assertRaises(ValueError):
                        frozen_launch_procargs(spoofed)

    def test_procargs_rejects_missing_duplicate_extra_and_bootstrap_named_env(self):
        _, _, environment = self._procargs_fixture()
        pairs = list(environment.items())
        candidates = [pairs[:-1], pairs[:-1] + [pairs[0]], pairs + [('EXTRA', '1')],
                      pairs + [('pfz', '0x1')], pairs + [('dyld_hw_tpro', '1')]]
        for entries in candidates:
            for length in range(8):
                with self.subTest(entries=[key for key, value in entries], length=length):
                    raw, _, _ = self._procargs_fixture(length, environment=entries)
                    with self.assertRaises(ValueError):
                        frozen_launch_procargs(raw)

    def test_procargs_rejects_unknown_repeated_reordered_or_malformed_bootstrap(self):
        for tail in ((b'EXTRA=1',), (b'dyld_hw_tpro=0',), (b'dyld_hw_tpro=1', b'dyld_hw_tpro=1'),
                     (b'dyld_hw_tpro_pagers=1', b'dyld_hw_tpro=1')):
            with self.subTest(tail=tail):
                raw, _, _ = self._procargs_fixture(tail=tail)
                with self.assertRaises(ValueError):
                    frozen_launch_procargs(raw)
        raw, _, _ = self._procargs_fixture()
        for changed in (raw[:-1], raw + bytes(8), raw.replace(b'pfz=0x1', b'pfz=bad'),
                        raw.replace(b'arm64e_abi=os', b'arm64e_abi=xx')):
            with self.assertRaises(ValueError):
                frozen_launch_procargs(changed)

    def test_inaccessible_process_prevents_global_pipe_acceptance(self):
        observer = object.__new__(MacProcessObserver)
        observer.pipe_holder_census = lambda endpoints: {
            'holders': endpoints, 'unavailable': [{'pid': 43, 'operation': 'PROC_PIDLISTFDS', 'errno': 1}]}
        with self.assertRaisesRegex(ValueError, '^lcer.pipe_holder_census_unavailable$'):
            observer.pipe_holders([])

    def test_raw_trace_hashes_actual_written_lines_and_rejects_before_write(self):
        with tempfile.TemporaryDirectory(prefix='city-raw-trace-', dir='/private/tmp') as directory:
            path = Path(directory) / 'harness.jsonl'
            writer = RawTraceWriter(CONTRACT_PATH.read_bytes(), path)
            self.addCleanup(writer.close)
            command = {'schema': 'city.live_evidence_command.v1', 'witness_id': 'W1', 'domain': 'domain_A',
                       'launch_id': 'fixture', 'operation_id': 'inspect_L0', 'binding_sha256': '0' * 64,
                       'command': 'inspect', 'payload': None}
            raw = stored_json_bytes(command)
            payload = {'direction': 'stdin', 'raw_line_utf8': raw.decode(), 'stream_byte_offset': 0, 'parsed_schema': 'command'}
            first = writer.append('wire_event', payload, 'domain_A', 'inspect_L0')
            first_raw = path.read_bytes()
            payload['stream_byte_offset'] = len(raw)
            command.update({'operation_id': 'shutdown_0001', 'command': 'shutdown'})
            payload['raw_line_utf8'] = stored_json_bytes(command).decode()
            second = writer.append('wire_event', payload, 'domain_A', 'shutdown_0001')
            self.assertIsNone(first['previous_event_sha256'])
            self.assertEqual(second['previous_event_sha256'], hashlib.sha256(first_raw).hexdigest())
            self.assertEqual(writer.rows()[0]['payload']['stream_byte_offset'], 0)
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, '^lcer.schema_invalid$'):
                writer.append('unknown_event', {})
            with self.assertRaisesRegex(ValueError, '^lcer.schema_invalid$'):
                writer.append('wire_event', {**payload, 'raw_line_utf8': '{}\n'}, 'domain_A', 'shutdown_0001')
            with self.assertRaisesRegex(ValueError, '^lcer.trace_relation_invalid$'):
                writer.append('wire_event', payload, 'domain_B', 'shutdown_0001')
            self.assertEqual(path.read_bytes(), before)
            with self.assertRaises(FileExistsError):
                RawTraceWriter(CONTRACT_PATH.read_bytes(), path)

    def test_helper_holds_proof_pipe_is_rejected_offline(self):
        endpoint = {'pid': 42, 'fd': 1, 'kind': 'pipe', 'kernel_id': '1' * 16, 'peer_kernel_id': '2' * 16,
                    'access': 'write', 'path': None}
        helper = {**endpoint, 'pid': 43, 'fd': 9}
        self.assertEqual(exact_pipe_holders([endpoint], [endpoint]), [endpoint])
        with self.assertRaisesRegex(ValueError, '^lcer.proof_pipe_extra_holder$'):
            exact_pipe_holders([endpoint], [endpoint, helper])
        with self.assertRaisesRegex(ValueError, '^lcer.original_pipe_identity_mismatch$'):
            exact_pipe_holders([endpoint], [])
        with self.assertRaisesRegex(ValueError, '^lcer.process_observation_invalid$'):
            exact_pipe_holders([endpoint], [endpoint, endpoint])

    def test_vmmap_requires_bound_process_and_real_executable_ranges(self):
        raw = (b'Process:         Fixture [42]\nParent Process:  Parent [41]\nPath: /fixture\n'
               b'Load Address: 0x1000\nTarget Type: live task\nAnalysis Tool: /usr/bin/vmmap\n'
               b'==== Non-writable regions for process 42\n'
               b'__TEXT 1000-2000 [ 4K 4K 0K 0K] r-x/r-x SM=COW /fixture\n'
               b'__TEXT 3000-4000 [ 4K 4K 0K 0K] r-x/r-x SM=COW /SDK Path/library\n'
               b'==== Writable regions for process 42\n==== Legend\n==== Summary for process 42\n'
               b'__TEXT 8K 8K 0K 0K 0K 0K 0K 2\n')
        self.assertEqual(vmmap_image_paths(raw, 42, 41, '/fixture'), ['/SDK Path/library', '/fixture'])
        for changed in [raw.replace(b'[42]', b'[43]'), raw.replace(b'3000-4000', b'1800-4000'),
                        raw.replace(b'1000-2000', b'broken'), raw.replace(b'live task', b'corpse'),
                        raw.replace(b'Load Address: 0x1000\n', b''),
                        raw.replace(b'0x1000', b'0x3000'), raw.replace(b'Path: /fixture', b'Path: /wrong'),
                        raw.replace(b'Load Address: 0x1000', b'Load Address: 0x1000\nLoad Address: 0x1000')]:
            with self.assertRaisesRegex(ValueError, '^lcer.process_images_invalid$'):
                vmmap_image_paths(changed, 42, 41, '/fixture')
        redacted = raw.replace(b'Path: /fixture', b'Path: /opt/homebrew/*/Python')
        self.assertEqual(vmmap_image_paths(redacted, 42, 41, '/fixture'), ['/SDK Path/library', '/fixture'])
        for changed in [redacted.replace(b'0x1000', b'0x3000'),
                        redacted.replace(b'SM=COW /fixture', b'SM=COW /impostor'),
                        redacted.replace(b'1000-2000', b'0800-2000'),
                        redacted.replace(b'/*/', b'/par*t/')]:
            with self.assertRaisesRegex(ValueError, '^lcer.process_images_invalid$'):
                vmmap_image_paths(changed, 42, 41, '/fixture')

    def _cache_fixture(self, directory):
        main = Path(directory) / 'dyld_shared_cache_arm64e'
        cache_uuid, sub_uuid, image_uuid = bytes(range(1, 17)), bytes(range(17, 33)), bytes(range(33, 49))
        base = 0x100000000
        first, second = bytearray(8192), bytearray(4096)
        for raw, uuid, address in [(first, cache_uuid, base), (second, sub_uuid, base + 8192)]:
            raw[:16] = b'dyld_v1  arm64e\0'
            struct.pack_into('<II', raw, 16, 512, 1)
            raw[88:104] = uuid
            struct.pack_into('<QQQII', raw, 512, address, len(raw), 0, 5, 5)
        struct.pack_into('<QQ', first, 136, 1056, 1)
        struct.pack_into('<II', first, 392, 1088, 1)
        struct.pack_into('<II', first, 448, 1024, 1)
        struct.pack_into('<QQQII', first, 1024, base + 4096, 0, 0, 1144, 0)
        first[1056:1072] = image_uuid
        struct.pack_into('<QII', first, 1072, base + 4096, 256, 1144)
        first[1088:1104] = sub_uuid
        struct.pack_into('<Q', first, 1104, 8192)
        first[1112:1116] = b'.01\0'
        name = b'/usr/lib/libfixture.dylib\0'
        first[1144:1144 + len(name)] = name
        struct.pack_into('<IiiIIIII', first, 4096, 0xfeedfacf, 0x0100000c, 2, 6, 1, 24, 0, 0)
        struct.pack_into('<II', first, 4128, 0x1b, 24)
        first[4136:4152] = image_uuid
        main.write_bytes(first)
        Path(str(main) + '.01').write_bytes(second)
        return main

    def test_cache_binds_subcache_bytes_and_embedded_macho_identity(self):
        with tempfile.TemporaryDirectory(prefix='city-cache-fixture-', dir='/private/tmp') as directory:
            main = self._cache_fixture(directory)
            result = dyld_cache_inventory(main)
            self.assertEqual(result['files'], [external_file_identity(main), external_file_identity(str(main) + '.01')])
            self.assertEqual(len(result['cache_uuids']), 2)
            self.assertEqual(result['images'], [{'realpath': '/usr/lib/libfixture.dylib',
                'sha256': result['main']['sha256'], 'macho_uuid': '21222324-2526-2728-292a-2b2c2d2e2f30',
                'architecture': 'arm64e', 'source': 'dyld_shared_cache'}])

    def test_image_reconciliation_rejects_missing_extra_and_forged_loader_rows(self):
        with tempfile.TemporaryDirectory(prefix='city-image-reconcile-', dir='/private/tmp') as directory:
            main = self._cache_fixture(directory)
            cache = dyld_cache_inventory(main)
            rows = cache['images']
            paths = [row['realpath'] for row in rows]
            self.assertEqual(reconcile_process_images(rows, paths, cache, 'arm64'), rows)
            changed = copy.deepcopy(rows); changed[0]['macho_uuid'] = '00000000-0000-0000-0000-000000000000'
            for reported, mappings in [(rows, []), ([], paths), (changed, paths), (rows + rows, paths), (rows, paths + paths)]:
                with self.assertRaisesRegex(ValueError, '^lcer.process_images_invalid$'):
                    reconcile_process_images(reported, mappings, cache, 'arm64')
            with self.assertRaisesRegex(ValueError, '^lcer.process_images_invalid$'):
                reconcile_process_images(rows, paths, cache, 'x86_64')

    def test_cache_accepts_only_exact_replicated_subcache_image_index(self):
        with tempfile.TemporaryDirectory(prefix='city-cache-replica-', dir='/private/tmp') as directory:
            main = self._cache_fixture(directory)
            first = main.read_bytes()
            sub = Path(str(main) + '.01')
            second = bytearray(sub.read_bytes())
            second[136:152] = first[136:152]
            second[448:456] = first[448:456]
            second[1024:1088] = first[1024:1088]
            second[1144:1200] = first[1144:1200]
            sub.write_bytes(second)
            self.assertEqual(len(dyld_cache_inventory(main)['images']), 1)
            second[1056] ^= 1
            sub.write_bytes(second)
            with self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_invalid$'):
                dyld_cache_inventory(main)

    def test_cache_rejects_forged_tables_uuid_ranges_and_subcache_paths(self):
        changes = [(4136, b'X'), (1056, b'Y'), (1112, b'../x\0'),
                   (512, struct.pack('<Q', 0)), (1072, struct.pack('<Q', 0xfffffffffffffff0)),
                   (448, struct.pack('<II', 1024, 2))]
        with tempfile.TemporaryDirectory(prefix='city-cache-adversary-', dir='/private/tmp') as directory:
            for offset, replacement in changes:
                with self.subTest(offset=offset):
                    main = self._cache_fixture(directory)
                    raw = bytearray(main.read_bytes())
                    raw[offset:offset + len(replacement)] = replacement
                    main.write_bytes(raw)
                    with self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_invalid$'):
                        dyld_cache_inventory(main)
            main = self._cache_fixture(directory)
            sub = Path(str(main) + '.01')
            raw = bytearray(sub.read_bytes()); raw[88] ^= 1; sub.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_invalid$'):
                dyld_cache_inventory(main)

    def test_clang_dependency_escaping_and_invalid_make_syntax(self):
        raw = b'/output.o: \\\n /SDK\\ Path/a.h /source/has\\#tag.h /source/dollar$$.h\n'
        self.assertEqual(clang_dependency_paths(raw),
                         (['/output.o'], ['/SDK Path/a.h', '/source/has#tag.h', '/source/dollar$.h']))
        for raw in [b'/output: $(shell anything)\n', b'/output: /a\n/second: /b\n', b'/output: /a # comment\n', b'/output:']:
            with self.assertRaisesRegex(ValueError, '^lcer.build_dependencies_invalid$'):
                clang_dependency_paths(raw)

    def test_action_graph_follows_dependencies_and_rejects_false_execution(self):
        def action(command, status, prerequisites, outputs):
            return {'command': command, 'description': 'Build', 'status': status, 'cwd': '/private/tmp',
                    'flags': [False] * 11, 'prerequisites': prerequisites, 'produced': outputs, 'dependency_list': None}
        graph = {'receipt': '/receipt', 'actions': [
            action('/compiler', 'object', ['/source.cpp'], ['/object.o']),
            action('/writer', 'receipt', ['/object.o'], ['/receipt']),
            action('/unused', 'template', ['/unused.cpp'], [])]}
        log = b'[1/2] Build object\n[2/2] Build receipt [NoUba]\nResult: Succeeded\n'
        result = build_action_prerequisites(graph, log)
        self.assertEqual(result, {'action_indices': [0, 1], 'executed_action_count': 2,
                                  'prerequisite_paths': ['/compiler', '/object.o', '/source.cpp', '/writer']})
        for changed in [log.replace(b'[1/2]', b'[2/2]'), log.replace(b'Build object', b'Build unlisted'),
                        log.replace(b'Succeeded', b'Failed'), log + b'Result: Failed\n',
                        log.replace(b'Result: Succeeded', b'Result: Succeeded suffix'),
                        log.replace(b'[1/2] ', b'[1/2]')]:
            with self.assertRaisesRegex(ValueError, '^lcer.build_execution_log_invalid$'):
                build_action_prerequisites(graph, changed)
        graph['actions'][0]['prerequisites'].append('/receipt')
        with self.assertRaisesRegex(ValueError, '^lcer.build_action_graph_invalid$'):
            build_action_prerequisites(graph, log)

    def test_archive_bounds_version_and_reference_types(self):
        for raw in [b'', struct.pack('<i', 36), struct.pack('<i', 37) + b'\x02',
                    struct.pack('<i', 37) + b'\x00' + b'\x00' * 8]:
            with self.assertRaisesRegex(ValueError, '^lcer.build_action_graph_invalid$'):
                UbtActionArchive(raw).actions()
        raw = struct.pack('<ii', 0, 5) + b'/file' + struct.pack('<i', 0)
        reader = UbtActionArchive(raw)
        self.assertEqual(reader.file_item(), '/file')
        with self.assertRaisesRegex(ValueError, '^lcer.build_action_graph_invalid$'):
            reader.directory_item()

    def test_lsof_nul_fields_preserve_path_whitespace(self):
        raw = b'p42\0\nf4\0ar\0tREG\0d1,2\0n/private/tmp/a name\nwith newline\0\n'
        self.assertEqual(parse_lsof_descriptors(raw, 42), [{"fd": 4, "access": "r", "type": "REG", "device": "1,2",
                                                          "name": "/private/tmp/a name\nwith newline"}])
        for changed in [raw.replace(b'p42', b'p41'), raw + b'f4\0', raw.replace(b'ar\0', b'ar\0aw\0')]:
            with self.assertRaisesRegex(ValueError, '^lcer.process_observation_invalid$'):
                parse_lsof_descriptors(changed, 42)

    def test_external_file_identity_hashes_raw_bytes_after_realpath(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            root = Path(directory).resolve()
            file = root / 'external.bin'; raw = b'\0external\nidentity\xff'; file.write_bytes(raw)
            alias = root / 'external-alias'; alias.symlink_to(file)
            expected = {'realpath': str(file), 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)}
            self.assertEqual(external_file_identity(file), expected)
            self.assertEqual(external_file_identity(alias), expected)

    def test_macho_rejects_truncated_and_duplicate_uuid_commands(self):
        uuid = bytes(range(16))
        command = struct.pack('<II', 0x1b, 24) + uuid
        header = struct.pack('<IiiIIIII', 0xfeedfacf, 0x0100000c, 0, 6, 1, 24, 0, 0)
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            file = Path(directory) / 'fixture.dylib'
            file.write_bytes(header + command)
            row, = macho_file_images(file)
            self.assertEqual((row['architecture'], row['macho_uuid']), ('arm64', '00010203-0405-0607-0809-0a0b0c0d0e0f'))
            duplicate = struct.pack('<IiiIIIII', 0xfeedfacf, 0x0100000c, 0, 6, 2, 48, 0, 0) + command * 2
            for raw in [header + command[:-1], header[:12], header + struct.pack('<II', 0x1b, 32) + uuid, duplicate]:
                file.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, '^lcer.image_identity_invalid$'):
                    macho_file_images(file)


class BuildActionInputInventoryTests(unittest.TestCase):
    """Actual temporary archive/receipt/depfile bytes; no compiler invocation."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='city-build-inputs-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.put('City/City.uproject', b'{}')
        self.engine = self.root / 'Engine'
        self.put('Engine/Build/Build.version', b'{"MajorVersion":5}')
        self.executable = self.put('Engine/Binaries/Mac/UnrealEditor', b'target executable')
        self.editor = self.put('Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor', b'editor executable')
        self.compiler = self.put('Tools/clang++', b'compiler identity')
        self.sdk = self.put('SDK With Spaces/SDKSettings.json', b'{"Version":"26"}').parent
        self.source = self.put('City/Source/Thing.cpp', b'int thing;')
        self.header = self.put('Engine/Source/Thing.h', b'extern int thing;')
        self.object = self.put('City/Intermediate/Thing.o', b'object output')
        self.depfile = self.put('City/Intermediate/Thing.d',
                               ('%s: %s %s\n' % (self.object, self.source, self.header)).encode())
        self.compile_rsp = self.put('City/Intermediate/compile.rsp',
                                    ('-c -arch arm64 -isysroot "%s" "%s" -o "%s"\n' %
                                     (self.sdk, self.source, self.object)).encode())
        image = struct.pack('<IiiIIIII', 0xfeedfacf, 0x0100000c, 0, 6, 1, 24, 0, 0)
        image += struct.pack('<II', 0x1b, 24) + bytes(range(16))
        self.module = self.put('City/Binaries/Mac/libUnrealEditor-City.dylib', image)
        self.link_rsp = self.put('City/Intermediate/link.rsp',
                                 ('-dynamiclib -arch arm64 -isysroot "%s" "%s" -o "%s"\n' %
                                  (self.sdk, self.object, self.module)).encode())
        self.writer = self.put('Tools/dotnet', b'metadata writer identity')
        self.program = self.put('Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll', b'UBT program identity')
        self.metadata = self.put('City/Intermediate/TargetMetadata.json', b'{}')
        self.receipt = self.put('City/Binaries/Mac/CityEditor.target', b'{}')
        self.receipt_value = {'TargetName': 'CityEditor', 'Platform': 'Mac', 'Configuration': 'Development',
                              'TargetType': 'Editor', 'Architecture': 'arm64', 'IsTestTarget': False,
                              'Project': '../../City.uproject',
                              'Launch': '$(EngineDir)/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor',
                              'BuildProducts': [{'Path': '$(EngineDir)/Binaries/Mac/UnrealEditor', 'Type': 'RequiredResource'},
                                                {'Path': '$(ProjectDir)/Binaries/Mac/libUnrealEditor-City.dylib',
                                                 'Type': 'DynamicLibrary'}]}
        self.archive = self.put('City/Intermediate/Build/Mac/arm64/CityEditor/Development/Makefile.bin', b'')
        self.actions = [self.action(3, self.compiler, self.compile_rsp, [self.source, self.compile_rsp],
                                   [self.object, self.depfile], self.depfile),
                        self.action(6, self.compiler, self.link_rsp, [self.object, self.link_rsp], [self.module]),
                        self.action(7, self.writer, None, [self.module, self.metadata], [self.receipt]),
                        self.action(3, self.compiler, None, [self.root / 'never-created.cpp'], [])]
        self.actions[2]['arguments'] = ('"%s" -Session="{00000000-0000-0000-0000-000000000000}" '
                                        '-Mode=WriteMetadata -Input="%s" -Version=2' % (self.program, self.metadata))
        self.log = b'[1/3] Build action0\n[2/3] Build action1\n[3/3] Build action2\nResult: Succeeded\n'
        self.save()

    def put(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return path

    def action(self, kind, command, response, prerequisites, outputs, dependency=None):
        return {'type': kind, 'command': str(command), 'cwd': str(self.engine / 'Source'),
                'arguments': '@"%s"' % response if response else '-Mode=WriteMetadata',
                'response_contents': response.read_text().splitlines() if response else [],
                'prerequisites': [str(path) for path in prerequisites], 'produced': [str(path) for path in outputs],
                'dependency_list': str(dependency) if dependency else None}

    def save(self):
        self.receipt.write_bytes(stored_json_bytes(self.receipt_value))
        data, references = bytearray(), {}
        def integer(value):
            data.extend(struct.pack('<i', value))
        def string(value):
            raw = value.encode() if value is not None else None
            integer(len(raw) if raw is not None else -1)
            if raw is not None:
                data.extend(raw)
        def sequence(values, emit):
            integer(len(values))
            for value in values:
                emit(value)
        def reference(kind, value):
            if value is None:
                integer(-1)
                return
            key = (kind, value)
            fresh = key not in references
            index = references.setdefault(key, len(references))
            integer(index)
            if fresh:
                string(value)
        integer(37); data.extend(b'\0' + bytes(8)); sequence([], string); string('')
        for value in (self.executable, self.receipt, self.archive.parent,
                      self.project.parent / 'Intermediate/Build/Mac' / getattr(self, 'target_name', 'CityEditor') / 'Development'):
            string(str(value))
        integer(1); data.extend(b'\0'); sequence([], string); data.extend(b'\0')
        for _ in range(8):
            sequence([], string)
        integer(len(self.actions))
        for index, action in enumerate(self.actions):
            reference('serializer', 'DefaultActionSerializer')
            data.extend(bytes([action['type'], 0]))
            for key in ('cwd', 'command', 'arguments'):
                string(action[key])
            sequence(action['response_contents'], string)
            for value in ('fixture compiler version', 'Build', 'action%d' % index):
                string(value)
            data.extend(bytes(11))
            for values in (action['prerequisites'], action['produced'], []):
                sequence(values, lambda value: reference('file', value))
            for _ in range(3):
                sequence([], string)
            data.extend(b'\0'); reference('file', action['dependency_list'])
            data.extend(bytes(2) + struct.pack('<dI', 1.0, 0))
        self.archive.write_bytes(data)

    def read(self):
        return BuildActionInputInventory(self.archive, self.log, self.project, self.engine, self.editor, 'CityEditor')

    def test_complete_dependency_closure_and_separate_executed_action_count(self):
        reader = self.read()
        result = reader.snapshot()
        self.assertEqual(result['action_indices'], [0, 1, 2])
        self.assertEqual(result['executed_action_count'], 3)
        paths = {row['realpath'] for row in result['build_inputs']}
        self.assertTrue({str(p) for p in (self.archive, self.receipt, self.source, self.header, self.depfile,
                                        self.compile_rsp, self.link_rsp, self.compiler, self.program,
                                        self.sdk / 'SDKSettings.json')} <= paths)
        self.assertNotIn(str(self.root / 'never-created.cpp'), paths)
        self.assertNotEqual(result['target_executable'], result['editor'])
        self.assertEqual(result['modules'], macho_file_images(self.module))
        result['build_inputs'].clear()
        self.assertTrue(reader.snapshot()['build_inputs'])
        self.log = b'Target is up to date\nResult: Succeeded\n'
        cached = self.read().snapshot()
        self.assertEqual(cached['action_indices'], [0, 1, 2])
        self.assertEqual(cached['executed_action_count'], 0)

    def test_receipt_target_project_architecture_and_editor_must_match(self):
        for field, value in [('TargetName', 'OtherEditor'), ('Platform', 'Win64'), ('Configuration', 'Shipping'),
                             ('Architecture', 'x86_64'), ('IsTestTarget', 0), ('Project', '../../Other.uproject'),
                             ('Launch', '$(EngineDir)/Binaries/Mac/UnrealEditor')]:
            with self.subTest(field=field):
                old = self.receipt_value[field]
                self.receipt_value[field] = value
                self.save()
                with self.assertRaises((ValueError, FileNotFoundError)):
                    self.read()
                self.receipt_value[field] = old
        self.save()

    def test_response_must_match_archive_and_be_a_prerequisite(self):
        self.compile_rsp.write_bytes(self.compile_rsp.read_bytes().replace(b'arm64', b'x86_64'))
        with self.assertRaisesRegex(ValueError, '^lcer.build_response_changed$'):
            self.read()
        self.compile_rsp.write_text('\n'.join(self.actions[0]['response_contents']) + '\n')
        self.actions[0]['prerequisites'].remove(str(self.compile_rsp)); self.save()
        with self.assertRaisesRegex(ValueError, '^lcer.build_response_invalid$'):
            self.read()

    def test_response_trailing_blank_lines_preserve_argument_identity(self):
        self.actions[1]['response_contents'].extend(['', ''])
        self.save()
        self.assertEqual(self.read().snapshot()['executed_action_count'], 3)

    def test_metadata_program_and_input_are_bound_without_executing_arguments(self):
        original = self.actions[2]['arguments']
        for value in [original.replace('UnrealBuildTool.dll', 'Unlisted.dll'),
                      original.replace('-Version=2', '-Version=3'),
                      original.replace(str(self.metadata), '/unlisted/input.json')]:
            self.actions[2]['arguments'] = value; self.save()
            with self.assertRaisesRegex(ValueError, '^lcer.build_metadata_action_invalid$'):
                self.read()

    def test_ambiguous_compiler_or_sdk_rejects(self):
        other = self.put('OtherTools/clang++', b'another compiler')
        self.actions[1]['command'] = str(other); self.save()
        with self.assertRaisesRegex(ValueError, '^lcer.build_toolchain_invalid$'):
            self.read()
        self.actions[1]['command'] = str(self.compiler)
        sdk = self.put('OtherSDK/SDKSettings.json', b'other SDK').parent
        self.link_rsp.write_text(self.link_rsp.read_text().replace(str(self.sdk), str(sdk)))
        self.actions[1]['response_contents'] = self.link_rsp.read_text().splitlines(); self.save()
        with self.assertRaisesRegex(ValueError, '^lcer.build_toolchain_invalid$'):
            self.read()

    def test_duplicate_or_wrong_architecture_flags_reject(self):
        original = self.compile_rsp.read_text()
        for text in [original.replace('arm64', 'x86_64'), original + '-isysroot /another\n',
                     original + '--sysroot=/another\n', original + '-isysroot/another\n',
                     original.replace('-arch arm64', '')]:
            self.compile_rsp.write_text(text)
            self.actions[0]['response_contents'] = text.splitlines(); self.save()
            with self.assertRaisesRegex(ValueError, '^lcer.build_toolchain_invalid$'):
                self.read()

    def test_receipt_and_final_linked_modules_must_have_exact_coverage(self):
        self.put('City/Binaries/Mac/orphan.dylib', self.module.read_bytes())
        self.receipt_value['BuildProducts'].append({'Path': '$(ProjectDir)/Binaries/Mac/orphan.dylib', 'Type': 'DynamicLibrary'})
        self.save()
        with self.assertRaisesRegex(ValueError, '^lcer.build_module_producer_missing$'):
            self.read()
        self.receipt_value['BuildProducts'] = self.receipt_value['BuildProducts'][:1]; self.save()
        with self.assertRaisesRegex(ValueError, '^lcer.build_module_producer_missing$'):
            self.read()

    def test_changed_dependency_bytes_invalidate_retained_inventory(self):
        reader = self.read()
        self.header.write_bytes(b'changed input')
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
            reader.snapshot()

    def test_project_symlink_rejects_even_with_identical_target_bytes(self):
        target = self.put('External/Thing.cpp', self.source.read_bytes())
        self.source.unlink(); self.source.symlink_to(target)
        with self.assertRaisesRegex(ValueError, '^lcer.dependency_path_invalid$'):
            self.read()

    def test_external_sdk_alias_is_resolved_and_rechecked(self):
        alias = self.root / 'CurrentSDK'
        alias.symlink_to(self.sdk, target_is_directory=True)
        for index, path in ((0, self.compile_rsp), (1, self.link_rsp)):
            path.write_text(path.read_text().replace(str(self.sdk), str(alias)))
            self.actions[index]['response_contents'] = path.read_text().splitlines()
        self.save()
        reader = self.read()
        self.assertEqual(reader.snapshot()['sdk']['realpath'], str(self.sdk / 'SDKSettings.json'))
        other = self.put('RetargetedSDK/SDKSettings.json', (self.sdk / 'SDKSettings.json').read_bytes()).parent
        alias.unlink(); alias.symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
            reader.snapshot()

    def test_response_subset_rejects_unclassified_quoting_and_nested_files(self):
        self.assertEqual(ubt_response_arguments(b'-I"path with spaces" -DVALUE=""\n'), ['-Ipath with spaces', '-DVALUE='])
        self.assertEqual(ubt_response_arguments(b'-rpath @loader_path/ -rpath @executable_path/ -install_name "@rpath/libCity.dylib"'),
                         ['-rpath', '@loader_path/', '-rpath', '@executable_path/', '-install_name', '@rpath/libCity.dylib'])
        self.assertEqual(ubt_response_arguments(b'-rpath "@loader_path/../../Shared/Epic Games/Engine/Binaries/Mac"'),
                         ['-rpath', '@loader_path/../../Shared/Epic Games/Engine/Binaries/Mac'])
        for raw in [b'"unterminated', b"'quoted'", b'path\\ space', b'@nested.rsp', b'\x00', b'\xff',
                    b'@rpath/libCity.dylib', b'-install_name @unexpected/libCity.dylib', b'-rpath @nested.rsp']:
            with self.assertRaisesRegex(ValueError, '^lcer.build_response_invalid$'):
                ubt_response_arguments(raw)

    def test_linker_path_cannot_mask_an_existing_response_file(self):
        self.link_rsp.write_bytes(self.link_rsp.read_bytes() + b'-install_name "@rpath/libCity.dylib"\n')
        self.actions[1]['response_contents'] = self.link_rsp.read_text().splitlines(); self.save()
        self.read()
        self.put('Engine/Source/rpath/libCity.dylib', b'--sysroot=/unexpected')
        with self.assertRaisesRegex(ValueError, '^lcer.build_response_invalid$'):
            self.read()


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


class IndependentBuildActionTests(unittest.TestCase):
    """Feed real temporary UBT bytes to the independent release verifier."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier
        # Reuse a byte fixture writer, not the producer's inventory verdict.
        self.fixture = BuildActionInputInventoryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.original = {str(p): p.read_bytes() for p in self.fixture.root.rglob('*') if p.is_file()}
        self.actions = copy.deepcopy(self.fixture.actions)
        self.receipt = copy.deepcopy(self.fixture.receipt_value)

    def restore(self):
        for path, raw in self.original.items():
            Path(path).write_bytes(raw)
        self.fixture.actions = copy.deepcopy(self.actions)
        self.fixture.receipt_value = copy.deepcopy(self.receipt)

    def records(self):
        return [external_file_identity(Path(path)) for path in sorted(self.original)]

    def read(self, records=None, log=None):
        fixture = self.fixture
        files = self.verifier.ExternalFileSnapshot(self.records() if records is None else records)
        return self.verifier.native_build_action_inventory(files, str(fixture.project), str(fixture.engine),
                    str(fixture.editor), getattr(fixture, 'target_name', 'CityEditor'), fixture.log if log is None else log)

    def test_raw_receipt_dependency_chain_and_incremental_log(self):
        result = self.read()
        self.assertEqual(result['action_indices'], [0, 1, 2])
        self.assertEqual(result['executed_action_count'], 3)
        required = {row['realpath'] for row in result['required_files']}
        self.assertTrue({str(p) for p in (self.fixture.source, self.fixture.header, self.fixture.object,
                         self.fixture.depfile, self.fixture.program, self.fixture.module, self.fixture.receipt)} <= required)
        self.assertEqual(result['modules'][0]['macho_uuid'], '00010203-0405-0607-0809-0a0b0c0d0e0f')
        self.assertNotEqual(result['target_executable'], result['editor'])
        incremental = self.read(log=b'Target is up to date\nResult: Succeeded\n')
        self.assertEqual(incremental['action_indices'], result['action_indices'])
        self.assertEqual(incremental['executed_action_count'], 0)

    def test_native_receipt_spacing_accepted_and_ambiguous_json_rejected(self):
        fixture = self.fixture
        fixture.receipt.write_bytes(json.dumps(fixture.receipt_value, indent='\t').encode())
        self.assertEqual(self.read()['modules'], fixture.read().snapshot()['modules'])
        for raw in (b'{"TargetName":"CityEditor","TargetName":"OtherEditor"}', b'{"x":{"y":1,"y":2}}',
                    b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e9999}', b'[]', b'{} {}', b'\xff'):
            fixture.receipt.write_bytes(raw)
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.read()
            with self.subTest(producer_raw=raw), self.assertRaisesRegex(ValueError, '^lcer.build_receipt_invalid$'):
                fixture.read()

    def test_each_required_file_must_be_declared(self):
        required = self.read()['required_files']
        records = self.records()
        for missing in required:
            with self.subTest(missing=missing['realpath']):
                with self.assertRaisesRegex(ValueError, '^lcer.build_input_missing$'):
                    self.read([row for row in records if row['realpath'] != missing['realpath']])

    def test_raw_archive_truncation_and_unclassified_serializer(self):
        raw = self.fixture.archive.read_bytes()
        for altered in (raw[:0], raw[:4], raw[:13], raw[:len(raw)//2], raw[:-1],
                        struct.pack('<i', 38) + raw[4:], raw[:4] + b'\2' + raw[5:],
                        raw.replace(b'DefaultActionSerializer', b'UnknownActionSerializer')):
            with self.subTest(size=len(altered)):
                with self.assertRaisesRegex(ValueError, '^lcer.build_action_(graph_invalid|serializer_unclassified)$'):
                    self.verifier.NativeUbtArchive(altered).decode()

    def test_cycle_duplicate_producer_and_missing_receipt_producer(self):
        for attack in ('cycle', 'duplicate', 'missing'):
            self.restore()
            if attack == 'cycle':
                self.fixture.actions[0]['prerequisites'].append(str(self.fixture.module))
            elif attack == 'duplicate':
                self.fixture.actions[3]['produced'].append(str(self.fixture.object))
            else:
                self.fixture.actions[2]['produced'].clear()
            self.fixture.save()
            with self.subTest(attack=attack), self.assertRaisesRegex(ValueError, '^lcer.build_action_graph_invalid$'):
                self.read()

    def test_actual_log_rejects_missing_duplicate_invented_and_malformed_rows(self):
        for log in (b'', b'Result: Failed\n', self.fixture.log + b'Result: Succeeded\n',
                    self.fixture.log.replace(b'[2/3]', b'[1/3]'),
                    self.fixture.log.replace(b'[2/3] Build action1\n', b''),
                    self.fixture.log.replace(b'action1', b'unknown'),
                    self.fixture.log.replace(b'[2/3]', b'[2]')):
            with self.subTest(log=log), self.assertRaisesRegex(ValueError, '^lcer.build_execution_log_invalid$'):
                self.read(log=log)
        self.assertEqual(self.read(log=self.fixture.log.replace(b'action1\n', b'action1 [NoUba]\n'))[
                         'executed_action_count'], 3)

    def test_response_bytes_and_archived_arguments_must_agree(self):
        self.fixture.compile_rsp.write_bytes(self.fixture.compile_rsp.read_bytes().replace(b'arm64', b'x86_64'))
        with self.assertRaisesRegex(ValueError, '^lcer.build_response_changed$'):
            self.read()
        self.fixture.actions[0]['response_contents'] = self.fixture.compile_rsp.read_text().splitlines()
        self.fixture.save()
        with self.assertRaisesRegex(ValueError, '^lcer.build_toolchain_invalid$'):
            self.read()

    def test_response_and_make_grammars_reject_hidden_expansion(self):
        response = self.verifier.native_ubt_arguments
        self.assertEqual(response(b'-I"two words" "" -install_name @rpath/libX.dylib'),
                         ['-Itwo words', '', '-install_name', '@rpath/libX.dylib'])
        for raw in (b'@/tmp/options', b'"unfinished', b'one"unfinished', b"'shell'", b'bad\\escape',
                    b'-install_name @rpath/../libX.dylib', b'-rpath @rpath/libX.dylib', b'\xff', b'\0'):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, '^lcer.build_response_invalid$'):
                response(raw)
        dep = self.verifier.native_clang_dependencies
        self.assertEqual(dep(b'object.o: dir/a\\ b.h \\\n money$$.h escaped\\:name.h\n'),
                         [['object.o'], ['dir/a b.h', 'money$.h', 'escaped:name.h']])
        for raw in (b'object.o', b'object.o:', b': input.h', b'one: two: three', b'one: $ENV', b'one: #comment',
                    b'one: trailing\\', b'\xff'):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, '^lcer.build_dependencies_invalid$'):
                dep(raw)

    def test_dependency_target_and_absent_header_reject(self):
        self.fixture.depfile.write_bytes(b'/wrong/object: /wrong/header\n')
        with self.assertRaisesRegex(ValueError, '^lcer.build_dependencies_invalid$'):
            self.read()
        self.restore()
        self.fixture.depfile.write_bytes(self.fixture.depfile.read_bytes() + b' /missing/header\n')
        with self.assertRaisesRegex(ValueError, '^lcer.build_input_path_invalid$'):
            self.read()

    def test_receipt_identity_and_module_producers_reject_even_after_rehash(self):
        for key, value in (('Architecture', 'x86_64'), ('IsTestTarget', 0), ('Platform', 'Linux'),
                           ('TargetName', 'OtherEditor'), ('Launch', '$(ProjectDir)/../outside')):
            self.restore()
            self.fixture.receipt_value[key] = value
            self.fixture.save()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, '^lcer.build_receipt_invalid$'):
                self.read()
        self.restore()
        self.fixture.receipt_value['BuildProducts'].pop()
        self.fixture.save()
        with self.assertRaisesRegex(ValueError, '^lcer.build_module_producer_missing$'):
            self.read()
        self.restore()
        self.fixture.module.write_bytes(self.fixture.module.read_bytes()[:12] + struct.pack('<I', 2)
                                       + self.fixture.module.read_bytes()[16:])
        with self.assertRaisesRegex(ValueError, '^lcer.image_identity_invalid$'):
            self.read()

    def test_byte_snapshot_change_and_unlisted_metadata_program_reject(self):
        records = self.records()
        self.fixture.source.write_bytes(b'changed code')
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_(changed|invalid)$'):
            self.read(records)
        self.restore()
        self.fixture.actions[2]['arguments'] = self.fixture.actions[2]['arguments'].replace('UnrealBuildTool.dll', 'OtherProgram.dll')
        self.fixture.save()
        with self.assertRaisesRegex(ValueError, '^lcer.build_metadata_action_invalid$'):
            self.read()

    def test_project_symlink_rejects_but_external_sdk_alias_is_resolved(self):
        fixture = self.fixture
        alias = fixture.root / 'SDK Alias'
        alias.symlink_to(fixture.sdk, target_is_directory=True)
        for index, response in ((0, fixture.compile_rsp), (1, fixture.link_rsp)):
            response.write_bytes(response.read_bytes().replace(str(fixture.sdk).encode(), str(alias).encode()))
            fixture.actions[index]['response_contents'] = response.read_text().splitlines()
        fixture.save()
        self.assertEqual(self.read()['sdk']['realpath'], str(fixture.sdk / 'SDKSettings.json'))
        moved = fixture.root / 'relocated-source.cpp'
        fixture.source.rename(moved)
        fixture.source.symlink_to(moved)
        with self.assertRaisesRegex(ValueError, '^lcer.dependency_path_invalid$'):
            self.read()

    def test_build_record_join_derives_inventory_and_rejects_omission(self):
        fixture = self.fixture
        fixture.target_name = 'CityMaterializationProofEditor'
        fixture.receipt = fixture.put('City/Binaries/Mac/' + fixture.target_name + '.target', b'{}')
        fixture.archive = fixture.put('City/Intermediate/Build/Mac/arm64/' + fixture.target_name + '/Development/Makefile.bin', b'')
        fixture.actions[2]['produced'] = [str(fixture.receipt)]
        fixture.receipt_value['TargetName'] = fixture.target_name
        fixture.save()
        self.original.update({str(p): p.read_bytes() for p in (fixture.receipt, fixture.archive)})
        observed = self.read()
        policy = json.loads(CONTRACT_PATH.read_bytes())
        build = schema_example(policy['wire_schemas']['build_record'], policy['wire_schemas'])
        build.update({key: observed[key] for key in ('project', 'editor', 'modules')})
        build['log'] = {'path': 'build.log', 'sha256': hashlib.sha256(fixture.log).hexdigest(), 'size_bytes': len(fixture.log)}
        build['external_inputs'].update({key: observed[key] for key in ('engine_root', 'engine_build_version', 'compiler', 'sdk')})
        build['external_inputs']['build_inputs'] = observed['required_files']
        files = self.verifier.ExternalFileSnapshot(self.records())
        check = self.verifier._build_action_relations
        self.assertEqual(check(policy, stored_json_bytes(build), fixture.log, files), observed)
        for change in ('compiler', 'module', 'missing', 'log'):
            altered = copy.deepcopy(build)
            if change == 'compiler':
                altered['external_inputs']['compiler']['sha256'] = '0' * 64
            elif change == 'module':
                altered['modules'][0]['macho_uuid'] = '00000000-0000-0000-0000-000000000000'
            elif change == 'missing':
                altered['external_inputs']['build_inputs'] = [row for row in observed['required_files']
                                                              if row['realpath'] != str(fixture.header)]
            else:
                altered['log']['sha256'] = '0' * 64
            with self.subTest(change=change), self.assertRaises(ValueError):
                check(policy, stored_json_bytes(altered), fixture.log, files)


class RuntimeBuildInputInventoryTests(unittest.TestCase):
    """Real file/image/cache bytes with explicit record fixtures, not Unreal."""

    def setUp(self):
        self.fixture = BuildActionInputInventoryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        image = bytearray(self.fixture.module.read_bytes())
        struct.pack_into('<I', image, 12, 2)
        image[-16:] = bytes(range(16, 32))
        self.fixture.editor.write_bytes(image)
        self.build = self.fixture.read()
        self.cache_path = ProcessByteParserTests()._cache_fixture(self.fixture.root)
        self.python = current_python_runtime()
        self.config = self.fixture.put('Engine/Config/Base.ini', b'[Fixture]\nEnabled=True\n')
        self.plugin = self.fixture.put('Engine/Plugins/Fixture.uplugin', b'{"Name":"Fixture"}')
        self.raw = CONTRACT_PATH.read_bytes()
        self.inventory = self.make_inventory()
        definitions = json.loads(self.raw)['wire_schemas']
        self.row = schema_example(definitions['process_observation'], definitions)
        self.row.update(pid=1234, ppid=123, cwd_realpath=str(self.fixture.root),
                        executable=external_file_identity(self.fixture.editor))
        startup = self.row['startup']
        startup.update(pid=1234, cwd_realpath=str(self.fixture.root), witness_id='W1', domain='domain_A', launch_id='first',
                       proof_module=macho_file_images(self.fixture.module)[0],
                       config_files=[external_file_identity(self.config)], enabled_plugins=[external_file_identity(self.plugin)])
        images = macho_file_images(self.fixture.editor) + macho_file_images(self.fixture.module) + self.inventory.cache['images']
        self.images(images)

    def make_inventory(self):
        return RuntimeBuildInputInventory(self.raw, self.build, self.cache_path, self.python, self.fixture.module)

    def images(self, rows):
        rows = sorted(rows, key=lambda row: row['realpath'])
        self.row['loaded_images'] = copy.deepcopy(rows)
        self.row['startup']['loaded_images'] = copy.deepcopy(rows)

    def test_inputs_join_actual_files_images_cache_and_multiple_launches(self):
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_incomplete$'):
            self.inventory.external_inputs()
        self.inventory.validate_observation(self.row)
        result = self.inventory.external_inputs()
        self.assertEqual(result['python'], self.python['executable'])
        self.assertEqual(result['engine_configs'], [external_file_identity(self.config)])
        self.assertEqual(result['engine_plugins'], [external_file_identity(self.plugin)])
        self.assertEqual(result['loaded_images'], self.row['loaded_images'])
        paths = {row['realpath'] for row in result['build_inputs']}
        self.assertTrue({row['realpath'] for row in self.inventory.cache['files']} <= paths)
        self.row['startup'].update(domain='domain_B', launch_id='second', pid=2345)
        self.row['pid'] = 2345
        self.inventory.validate_observation(self.row)
        self.inventory.require_launches([{'witness_id': 'W1', 'domain': domain, 'launch_id': launch}
                                         for domain, launch in [('domain_A', 'first'), ('domain_B', 'second')]])
        result['loaded_images'].clear()
        self.assertTrue(self.inventory.external_inputs()['loaded_images'])

    def test_metadata_only_build_cannot_attach_runtime_inputs_to_an_acquisition_cohort(self):
        workspace = AcquisitionWorkspace(self.raw, CONTRACT_PATH.parent.parent,
                                          self.fixture.root / 'runtime', self.fixture.root / 'output')
        workspace.reserve()
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_build_capture_missing$'):
            AcquisitionProcessCohort(workspace, 'W1', self.inventory.cache, CaptureBudget(1048576),
                                     runtime_inputs=self.inventory)
        self.assertEqual(workspace._cases, set())
        self.assertFalse((self.fixture.root / 'output/W1').exists())

    def test_build_module_and_editor_must_both_be_observed(self):
        original = copy.deepcopy(self.row['loaded_images'])
        for path in (str(self.fixture.editor), str(self.fixture.module)):
            inventory = self.make_inventory()
            self.images([row for row in original if row['realpath'] != path])
            with self.assertRaisesRegex(ValueError, '^lcer.runtime_build_identity_mismatch$'):
                inventory.validate_observation(self.row)

    def test_forged_executable_or_proof_module_rejects(self):
        for field in ('executable', 'proof_module'):
            inventory = self.make_inventory()
            row = copy.deepcopy(self.row)
            if field == 'executable':
                row['executable']['sha256'] = '0' * 64
            else:
                row['startup']['proof_module']['macho_uuid'] = '00000000-0000-0000-0000-000000000000'
            with self.assertRaisesRegex(ValueError, '^lcer.runtime_build_identity_mismatch$'):
                inventory.validate_observation(row)

    def test_rehashed_changed_config_is_terminal_even_after_restoring_bytes(self):
        self.inventory.validate_observation(self.row)
        before = self.config.read_bytes()
        self.config.write_bytes(before + b'Changed=True\n')
        self.row['startup']['config_files'] = [external_file_identity(self.config)]
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
            self.inventory.validate_observation(self.row)
        self.config.write_bytes(before)
        self.row['startup']['config_files'] = [external_file_identity(self.config)]
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_failed$'):
            self.inventory.validate_observation(self.row)
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_incomplete$'):
            self.inventory.external_inputs()

    def test_plugin_membership_drift_rejects_even_when_every_file_is_valid(self):
        self.inventory.validate_observation(self.row)
        second = self.fixture.put('Engine/Plugins/Second.uplugin', b'{"Name":"Second"}')
        self.row['startup']['enabled_plugins'].append(external_file_identity(second))
        self.row['startup']['enabled_plugins'].sort(key=lambda row: row['realpath'])
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_changed$'):
            self.inventory.validate_observation(self.row)

    def test_loaded_image_membership_cannot_change_between_launches(self):
        self.inventory.validate_observation(self.row)
        self.images([row for row in self.row['loaded_images'] if row['source'] != 'dyld_shared_cache'])
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_changed$'):
            self.inventory.validate_observation(self.row)

    def test_launch_id_cannot_move_to_another_process(self):
        self.inventory.validate_observation(self.row)
        self.row['pid'] = self.row['startup']['pid'] = 9876
        with self.assertRaisesRegex(ValueError, '^lcer.original_process_identity_mismatch$'):
            self.inventory.validate_observation(self.row)

    def test_launch_coverage_rejects_missing_extra_and_duplicate_rows(self):
        self.inventory.validate_observation(self.row)
        first = {'witness_id': 'W1', 'domain': 'domain_A', 'launch_id': 'first'}
        for rows in ([], [first, first], [first, {**first, 'launch_id': 'unobserved'}]):
            with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_launches_incomplete$'):
                self.inventory.require_launches(rows)
        self.inventory.require_launches([first])

    def test_changed_cache_subfile_blocks_later_input_export(self):
        self.inventory.validate_observation(self.row)
        sub = Path(str(self.cache_path) + '.01')
        original = sub.read_bytes()
        sub.write_bytes(original + b'changed')
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
            self.inventory.external_inputs()
        sub.write_bytes(original)
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_incomplete$'):
            self.inventory.external_inputs()

    def test_changed_bound_loader_observation_is_terminal(self):
        from unittest import mock
        import live_cross_domain_evidence_round_trip_harness as harness
        self.inventory.validate_observation(self.row)
        before = current_dyld_process()
        self.inventory._cache_process_raw = stored_json_bytes(before)
        with mock.patch.object(harness, 'current_dyld_process', return_value={**before, 'image_count': before['image_count'] + 1}):
            with self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_observation_changed$'):
                self.inventory.external_inputs()
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_incomplete$'):
            self.inventory.external_inputs()

    def test_live_image_bytes_are_rechecked_before_input_export(self):
        external = self.fixture.put('External/library.dylib', self.fixture.module.read_bytes())
        self.images(self.row['loaded_images'] + macho_file_images(external))
        self.inventory.validate_observation(self.row)
        external.write_bytes(external.read_bytes() + b'changed bytes')
        with self.assertRaisesRegex(ValueError, '^lcer.process_images_invalid$'):
            self.inventory.external_inputs()


class RuntimeNativeWorldTests(unittest.TestCase):
    """Real native decoding with explicit build/process metadata fixtures.

    Copied headers and installed images are actual bytes. No build or Unreal
    process is run, and manually extended fixture inputs confer no live proof.
    """

    def setUp(self):
        self.fixture = RuntimeBuildInputInventoryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.inventory = self.fixture.inventory
        engine = Path('/Users/Shared/Epic Games/UE_5.8/Engine')
        plugin = CONTRACT_PATH.parent.parent / 'CityMaterializationProof/Plugins/CityLiveEvidenceProof'
        sources = [engine / 'Intermediate/Build/Mac/UnrealEditor/Inc/Engine/UHT' / (name + '.generated.h')
                   for name in ('Actor', 'Pawn', 'Controller', 'PlayerController', 'Info', 'GameModeBase')]
        sources.append(engine / 'Intermediate/Build/Mac/UnrealEditor/Inc/CoreUObject/UHT/Object.generated.h')
        sources.extend(plugin / 'Intermediate/Build/Mac/UnrealEditor/Inc/CityLiveEvidenceProof/UHT' / name
                       for name in ('CityLiveEvidenceActors.generated.h', 'CityLiveEvidenceGameMode.generated.h'))
        self.headers = []
        for source in sources:
            path = self.fixture.fixture.put('BoundHeaders/' + source.name, source.read_bytes())
            self.inventory._build._pin(path)
            self.headers.append(path)
        layout = 'Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h'
        target = Path(self.inventory._build.snapshot()['engine_root']) / layout
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((engine / layout).read_bytes())
        self.inventory._build._pin(target)
        self.inventory._build_raw = stored_json_bytes(self.inventory._build.snapshot())
        images = list(self.fixture.row['loaded_images'])
        paths = [engine / 'Binaries/Mac' / ('libUnrealEditor-' + name + '.dylib') for name in ('CoreUObject', 'Engine')]
        paths.append(plugin / 'Binaries/Mac/libUnrealEditor-CityLiveEvidenceProof.dylib')
        for path in paths:
            images.extend(row for row in macho_file_images(path) if row['architecture'] == 'arm64')
        self.fixture.images(images)

    def test_native_ancestry_requires_observation_then_decodes_bound_bytes(self):
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_incomplete$'):
            self.inventory.native_class_parents()
        self.inventory.validate_observation(self.fixture.row)
        parents = self.inventory.native_class_parents()
        self.assertEqual(parents['/Script/Engine.Pawn'], '/Script/Engine.Actor')
        self.assertEqual(parents['/Script/Engine.PlayerController'], '/Script/Engine.Controller')
        self.assertEqual(parents['/Script/CityLiveEvidenceProof.CityLiveEvidenceGameMode'], '/Script/Engine.GameModeBase')
        self.assertEqual(parents['/Script/CityLiveEvidenceProof.CityLiveEvidenceActor'], '/Script/Engine.Actor')
        parents['/Script/Engine.Pawn'] = None
        self.assertEqual(self.inventory.native_class_parents()['/Script/Engine.Pawn'], '/Script/Engine.Actor')

    def test_changed_header_invalidates_cached_ancestry_and_restoration_does_not_reopen_it(self):
        self.inventory.validate_observation(self.fixture.row)
        self.inventory.native_class_parents()
        path = self.headers[0]
        raw = path.read_bytes()
        path.write_bytes(raw + b'changed metadata')
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
            self.inventory.native_class_parents()
        path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_incomplete$'):
            self.inventory.native_class_parents()

    def test_cached_graph_mutation_is_terminal(self):
        self.inventory.validate_observation(self.fixture.row)
        parents = self.inventory.native_class_parents()
        parents['/Script/Engine.Pawn'] = None
        self.inventory._native_parents_raw = stored_json_bytes(parents)
        with self.assertRaisesRegex(ValueError, '^lcer.native_ancestry_invalid$'):
            self.inventory.native_class_parents()
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_incomplete$'):
            self.inventory.native_class_parents()

    def test_world_factory_rejects_unbound_metadata_and_defers_until_actual_startup_inputs(self):
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_build_capture_missing$'):
            LiveWorldAcceptance.from_runtime_inputs(self.fixture.raw, self.inventory)
        # Isolate the factory's lazy join. Production obtains this binding only
        # through from_workspace, which the captured-build tests cover.
        workspace = mock.Mock(spec=AcquisitionWorkspace)
        self.inventory._build._workspace = workspace
        self.inventory._build._capture_raw = stored_json_bytes({'python_runtime': self.fixture.python})
        workspace._build_capture = {'python_runtime': self.fixture.python}
        self.inventory._build._invocation_log = external_file_identity(self.headers[0])
        world = LiveWorldAcceptance.from_runtime_inputs(self.fixture.raw, self.inventory)
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_incomplete$'):
            world.census([])
        self.inventory.validate_observation(self.fixture.row)
        facts = world.census([])
        self.assertTrue(facts['wrong_world'])
        self.assertEqual(world._ancestry('/Script/Engine.PlayerController'),
                         {'/Script/Engine.PlayerController', '/Script/Engine.Controller',
                          '/Script/Engine.Actor', '/Script/CoreUObject.Object'})


class AcquisitionExecutionTests(unittest.TestCase):
    """Coordinator ownership tests with explicitly intercepted live producers.

    Real frozen policy, directories and launch-argument derivation execute.
    Audit, compiler, process execution and package production are fixtures.
    No intercepted result is audit acceptance, live evidence or a release.
    """

    def setUp(self):
        fixture = AcquisitionWorkspaceTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.workspace = fixture.workspace()
        self.execution = AcquisitionExecution(self.workspace, CaptureBudget(1024 * 1024))
        self.policy = json.loads(fixture.raw)
        self.cohorts, self.launches = [], []

    def run_fixture(self, failure=None):
        import live_cross_domain_evidence_round_trip_harness as harness
        inventory = mock.Mock(spec=RuntimeBuildInputInventory)
        inventory.cache = {}
        inventory._build = mock.Mock()
        inventory._build._workspace = self.workspace
        inventory.validator = FrozenWireValidator(self.fixture.raw)
        audit = schema_example(self.policy['wire_schemas']['source_audit'], self.policy['wire_schemas'])
        audit['returncode'] = 0
        writer = mock.Mock(spec=AcquisitionPackageWriter)
        writer.finalize.return_value = {'byte_graph_complete': True, 'live_acceptance_verified': False}
        self.writer = writer

        def case(cohort, world):
            self.cohorts.append(cohort)
            if failure == 'constructor':
                raise KeyboardInterrupt('offline constructor interruption')
            def execute_case():
                for domain, replacement in [('domain_A', False), ('domain_B', False)] + ([('domain_A', True)] if cohort.case_id == 'F07' else []):
                    launch = self.workspace.prepare_launch(cohort.case_id, domain, replacement)
                    self.launches.append(launch)
                    cohort._entries['replacement' if replacement else domain] = {'launch': launch}
                # The case producer is intercepted, including its process
                # cleanup. Constructor-interruption tests use real cleanup.
                cohort._closed = True
                selected = select_frozen_case(self.fixture.raw, cohort.case_id)
                status = 'acquisition_failure' if failure == cohort.case_id else ('accepted' if selected['kind'] == 'witness' else 'expected_failure')
                if failure == 'wrong_status:' + cohort.case_id:
                    status = 'expected_failure' if status == 'accepted' else 'accepted'
                return {'status': status}
            result = mock.Mock()
            result.execute_case.side_effect = execute_case
            return result

        with mock.patch.object(self.workspace, '_require_build_source_audit', return_value=audit), \
                mock.patch.object(self.workspace, 'build_candidate') as compiler, \
                mock.patch.object(harness, 'AcquisitionPackageWriter', return_value=writer), \
                mock.patch.object(RuntimeBuildInputInventory, 'from_workspace', return_value=inventory), \
                mock.patch.object(harness, 'CasePrefixExecution', side_effect=case):
            result = self.execution.execute()
        self.assertEqual(compiler.call_count, 1)
        return result

    def test_real_incomplete_audit_rejects_before_roots_and_consumes_attempt(self):
        self.workspace._source_audit = {'returncode': 0, 'source_audit_complete': True}
        with mock.patch.object(subprocess, 'run') as compiler:
            with self.assertRaisesRegex(ValueError, '^lcer.acquisition_implementation_incomplete$'):
                self.execution.execute()
            with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
                self.execution.execute()
        compiler.assert_not_called()
        self.assertEqual(list(self.fixture.context.iterdir()), [])

    def test_coordinator_covers_all_frozen_cases_and_exact_original_replacement_launches(self):
        self.assertEqual(self.run_fixture(), {'byte_graph_complete': True, 'live_acceptance_verified': False})
        self.assertEqual([cohort.case_id for cohort in self.cohorts], self.policy['artifact_hash_graph']['case_ids'])
        self.assertEqual(len(self.cohorts), 35)
        self.assertEqual(len(self.launches), 71)
        self.assertEqual(len({row['launch_id'] for row in self.launches}), 71)
        replacements = [row for row in self.launches if Path(row['process_root_realpath']).name == 'replacement']
        self.assertEqual([(row['witness_id'], row['domain']) for row in replacements], [('F07', 'domain_A')])
        self.assertTrue(all(cohort.trace.stream.closed and cohort._closed for cohort in self.cohorts))
        observed = self.writer.observed_build_record.call_args.args[2]
        self.assertEqual(observed, [{k: row[k] for k in ('witness_id', 'domain', 'launch_id')} for row in self.launches])
        self.writer.write_build.assert_called_once()
        self.writer.finalize.assert_called_once()
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            self.execution.execute()

    def test_nonzero_audit_result_cannot_reach_reservation_or_build(self):
        audit = schema_example(self.policy['wire_schemas']['source_audit'], self.policy['wire_schemas'])
        audit['returncode'] = 17
        with mock.patch.object(self.workspace, '_require_build_source_audit', return_value=audit), \
                mock.patch.object(self.workspace, 'build_candidate') as compiler:
            with self.assertRaisesRegex(ValueError, '^lcer.source_audit_record_invalid$'):
                self.execution.execute()
        compiler.assert_not_called()
        self.assertEqual(list(self.fixture.context.iterdir()), [])

    def test_case_outcome_cannot_be_relabelled_to_the_opposite_kind(self):
        failed = self.policy['artifact_hash_graph']['case_ids'][0]
        with self.assertRaisesRegex(ValueError, '^lcer.case_execution_failed$'):
            self.run_fixture('wrong_status:' + failed)
        self.assertEqual(len(self.cohorts), 1)
        self.writer.observed_build_record.assert_not_called()
        self.writer.finalize.assert_not_called()

    def test_failed_case_stops_sequence_without_fabricating_remaining_cases_or_release(self):
        failed = self.policy['artifact_hash_graph']['case_ids'][1]
        with self.assertRaisesRegex(ValueError, '^lcer.case_execution_failed$'):
            self.run_fixture(failed)
        self.assertEqual(len(self.cohorts), 2)
        self.assertTrue(all(cohort.trace.stream.closed and cohort._closed for cohort in self.cohorts))
        self.writer.observed_build_record.assert_not_called()
        self.writer.finalize.assert_not_called()

    def test_case_constructor_interruption_still_closes_owned_cohort_and_trace(self):
        with self.assertRaisesRegex(KeyboardInterrupt, '^offline constructor interruption$'):
            self.run_fixture('constructor')
        self.assertEqual(len(self.cohorts), 1)
        self.assertTrue(self.cohorts[0]._closed)
        self.assertTrue(self.cohorts[0].trace.stream.closed)
        self.writer.finalize.assert_not_called()

    def test_normal_command_dispatches_coordinator_without_an_opt_in_flag(self):
        import contextlib, io
        import live_cross_domain_evidence_round_trip_harness as harness
        output = io.StringIO()
        result = {'byte_graph_complete': True, 'live_acceptance_verified': False}
        with mock.patch.object(AcquisitionExecution, 'execute', return_value=result) as execute, contextlib.redirect_stdout(output):
            returned = harness.main(['acquire', '--runtime-parent', str(self.fixture.runtime), '--output', str(self.fixture.output)])
        execute.assert_called_once()
        self.assertEqual(returned, result)
        self.assertEqual(json.loads(output.getvalue()), result)
        self.assertEqual(list(self.fixture.context.iterdir()), [])


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


class CapturedCanonicalExecutionTests(unittest.TestCase):
    """Synthetic captures exercise real canonical calls, never live acceptance."""

    def setUp(self):
        import concurrent_external_evidence_arbitration as canonical
        self.canonical = canonical
        self.raw = CONTRACT_PATH.read_bytes()
        self.plan = FrozenObligationPlanCompiler(self.raw).compile()
        self.definitions = self.plan['constitutional_policy']['wire_schemas']
        self.directory = tempfile.TemporaryDirectory(prefix='city-capture-adapter-', dir='/private/tmp')
        self.addCleanup(self.directory.cleanup)

    def execution(self, case):
        trace = RawTraceWriter(self.raw, Path(self.directory.name) / (case + '.jsonl'))
        self.addCleanup(trace.close)
        execution = CapturedCanonicalExecution(self.raw, case, trace)
        captures = {}
        r0 = self.canonical.initial_canonical_envelope()
        for domain in ('domain_A', 'domain_B'):
            binding = schema_example(self.definitions['process_binding'], self.definitions)
            binding.update(witness_id=case, domain=domain, launch_id='offline_' + case + '_' + domain)
            execution.retain_binding(binding)
            q = self.canonical.external_evidence_q(r0, domain)
            raw = stored_json_bytes(q)
            routing = {'witness_id': case, 'domain': domain, 'launch_id': binding['launch_id'], 'operation_id': 'emit_0001',
                       'binding_sha256': hashlib.sha256(stored_json_bytes(binding)).hexdigest()}
            fields = {'physical_event_id': q['physical_event_id'], 'interaction_counter': 1,
                      'q_raw_sha256': hashlib.sha256(raw).hexdigest(), 'q_canonical_hash': self.canonical.q_hash(q)}
            capture = {'q_raw_utf8': raw.decode('utf-8'),
                       'acceptance_receipt_raw_utf8': stored_json_bytes(self.canonical.materialization_acceptance_receipt(r0, domain, binding['launch_id'])).decode('utf-8'),
                       'emission_receipt_raw_utf8': stored_json_bytes(self.canonical.evidence_emission_receipt(r0, q, domain, binding['launch_id'])).decode('utf-8'),
                       'wrapper': {'schema': 'city.live_evidence_emission.v1', **routing, **fields, 'source_record_hash': self.canonical.canonical_hash(r0)},
                       'physical_event': {'schema': 'city.live_evidence_physical_event.v1', **routing, **fields,
                                          'actor_id': 'offline_physical_fixture_' + domain,
                                          'accepted_record_raw_sha256': hashlib.sha256(stored_json_bytes(r0)).hexdigest()}}
            captures[domain] = stored_json_bytes(capture)
        return execution, trace, captures

    def test_all_frozen_canonical_prefixes_from_retained_capture_bytes(self):
        for case, plan in self.plan['frozen_case_plans'].items():
            with self.subTest(case=case):
                execution, trace, captures = self.execution(case)
                for domain, raw in captures.items(): execution.retain_capture(domain, raw)
                count = execution._core.canonical_coverage()['expected_call_count']
                for _ in range(count): execution.next_call()
                coverage = execution._core.canonical_coverage()
                self.assertTrue(coverage['canonical_prefix_complete'])
                self.assertEqual(coverage['publication_count'], plan['publication_count'])
                self.assertEqual(len(trace.rows()), count)
                for row, retained in zip(trace.rows(), execution._core.retained_calls()):
                    self.assertEqual(row['payload'], retained)
                self.assertEqual(execution.captures(), [{'domain': domain, 'emission': parse_stored_json(captures[domain])}
                                                        for domain in ('domain_A', 'domain_B')])

    def test_r1_delivery_requires_actual_publication_and_has_no_r0_receipt(self):
        execution, _, captures = self.execution('W1')
        r0 = execution.materialize_input('domain_A', 'materialize_0001')
        self.assertEqual(r0['record_raw_utf8'].encode(), execution.head_raw)
        self.assertIsInstance(r0['launch_receipt_raw_utf8'], str)
        with self.assertRaisesRegex(ValueError, '^lcer.committed_record_required$'):
            execution.materialize_input('domain_A', 'materialize_0002')
        for domain, raw in captures.items(): execution.retain_capture(domain, raw)
        for _ in range(4): execution.next_call()
        r1 = execution.materialize_input('domain_B', 'materialize_0002')
        self.assertEqual(r1['record_raw_utf8'].encode(), execution.head_raw)
        self.assertIsNone(r1['launch_receipt_raw_utf8'])
        self.assertEqual((r1['projection']['record_role'], r1['projection']['generation'], r1['projection']['allocation_owner']),
                         ('R1', 1, 'domain_A'))
        with self.assertRaisesRegex(ValueError, '^lcer.committed_record_required$'):
            execution.materialize_input('domain_A', 'materialize_0001')

    def test_changed_capture_or_receipt_cannot_supply_an_admission(self):
        execution, _, captures = self.execution('W1')
        with self.assertRaisesRegex(ValueError, '^lcer.capture_missing$'):
            execution.next_call()
        original = parse_stored_json(captures['domain_A'])
        changed = copy.deepcopy(original); changed['q_raw_utf8'] = changed['q_raw_utf8'][:-1]
        with self.assertRaisesRegex(ValueError, '^lcer.capture_bytes_invalid$'):
            execution.retain_capture('domain_A', stored_json_bytes(changed))
        changed = copy.deepcopy(original); receipt = parse_stored_json(changed['emission_receipt_raw_utf8'].encode())
        receipt['process_instance_id'] = 'other_process'; changed['emission_receipt_raw_utf8'] = stored_json_bytes(receipt).decode()
        with self.assertRaisesRegex(ValueError, '^lcer.binding_mismatch$'):
            execution.retain_capture('domain_A', stored_json_bytes(changed))
        execution.retain_capture('domain_A', captures['domain_A'])
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            execution.retain_capture('domain_A', captures['domain_A'])
        execution.next_call()
        self.assertEqual(execution.publication_count, 0)

    def test_trace_failure_after_resolve_preserves_r1_and_prevents_retry(self):
        execution, trace, captures = self.execution('W1')
        for domain, raw in captures.items(): execution.retain_capture(domain, raw)
        for _ in range(3): execution.next_call()
        trace.close()
        with self.assertRaises(ValueError): execution.next_call()
        self.assertEqual(execution.publication_count, 1)
        after = execution.head_raw
        with self.assertRaisesRegex(ValueError, '^lcer.core_sequence_invalid$'): execution.next_call()
        self.assertEqual(execution.head_raw, after)


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


class AcquisitionProcessCohortTests(unittest.TestCase):
    """Ownership fixtures plus actual interpreter cleanup; no Unreal proof."""

    def setUp(self):
        from unittest import mock
        import live_cross_domain_evidence_round_trip_harness as harness
        self.mock, self.harness = mock, harness
        temporary = tempfile.TemporaryDirectory(prefix='city-cohort-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.context = Path(temporary.name)
        self.workspace = AcquisitionWorkspace(CONTRACT_PATH.read_bytes(), CONTRACT_PATH.parent.parent,
                                              self.context / 'runtime', self.context / 'artifacts')
        self.workspace.reserve()
        self.events, self.processes, self.connections = [], [], []
        self.fail_monitor = None
        self.fail_startup = None
        self.fail_drain = None
        self.fail_sample = None

    def fixture(self, case='W1'):
        from types import SimpleNamespace
        test = self

        class Process:
            def __init__(self, observer):
                self.label = ('domain_A', 'domain_B', 'replacement')[len(test.processes)]
                self.pid = 100 + len(test.processes)
                self.returncode = None
                self.exec_descriptors = []
                self.timed_out = False
                test.processes.append(self)

            def start(self, argv, environment, cwd):
                test.events.append(('start', self.label))
                test.assertEqual(cwd, '/Users/boandersson/Projects/CITY')
                test.assertEqual(len(argv), 13)
                test.assertEqual(len(environment), 7)

            def resume(self): test.events.append(('resume', self.label))
            def poll(self): return self.returncode

            def wait(self, timeout):
                test.events.append(('wait', self.label))
                if self.timed_out and self.returncode is None:
                    raise TimeoutError('lcer.process_exit_timeout')
                if self.returncode is None: self.returncode = 0
                return self.returncode

            def send_signal(self, value):
                test.assertIn(value, (signal.SIGKILL, signal.SIGTERM))
                test.events.append(('kill' if value == signal.SIGKILL else 'terminate', self.label))
                self.returncode = -int(value)
                return True

            def close_pipes(self): test.events.append(('close', self.label))
            def observe_original_holders(self): test.events.append(('holders', self.label))

        class Monitor:
            def __init__(self, process, stdout, stderr, budget):
                self.process, self._started = process, False
                self._thread = SimpleNamespace(is_alive=lambda: False)
                test.assertEqual(stdout.name, process.label + '.stdout.log')
                test.assertEqual(stderr.name, process.label + '.stderr.log')
                if process.label == test.fail_monitor:
                    raise OSError('fixture_monitor_failure')

            def start(self):
                self._started = True
                test.events.append(('monitor', self.process.label))

            def finish(self, timeout):
                test.events.append(('drain', self.process.label))
                if self.process.label == test.fail_drain: raise OSError('fixture_drain_failure')
                return {'fixture': self.process.label}

        class Connection:
            def __init__(self, raw, case, domain, launch, monitor, trace):
                self.monitor, self.trace = monitor, trace
                self.startup_raw = None
                self.binding_sha256 = None
                self._failed = self._shutdown = False
                test.connections.append(self)

            def read_startup(self, timeout):
                label = self.monitor.process.label
                test.events.append(('ready', label))
                if label == test.fail_startup: raise ValueError('fixture_startup_failure')
                self.startup_raw = stored_json_bytes({'fixture': label})
                return {'fixture': label}

            def request(self, command, operation, timeout):
                test.events.append((command, self.monitor.process.label))
                test.assertEqual((command, operation), ('shutdown', 'shutdown_0001'))
                self._shutdown = True
                return {'response': {'status': 'ok'}}

        class Evidence:
            def __init__(self, raw, connection, cache): self.connection = connection

            def sample(self, checkpoint):
                label = self.connection.monitor.process.label
                test.events.append((checkpoint, label))
                if label == test.fail_sample: raise ValueError('fixture_holder_failure')
                return {'fixture': label, 'checkpoint': checkpoint}

        for name, value in [('OriginalPipeProcess', Process), ('OriginalPipeMonitor', Monitor),
                            ('OriginalProtocolConnection', Connection), ('OriginalProcessEvidence', Evidence),
                            ('MacProcessObserver', lambda: None)]:
            patch = self.mock.patch.object(self.harness, name, value)
            patch.start(); self.addCleanup(patch.stop)
        cohort = AcquisitionProcessCohort(self.workspace, case, {}, CaptureBudget(1048576))
        self.addCleanup(cohort.trace.close)
        self.addCleanup(cohort.cleanup, 0.2)
        return cohort

    def test_frozen_process_action_terminates_only_its_original_once(self):
        cohort = self.fixture('F08')
        cohort.start_originals(); cohort.read_startups()
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            cohort.terminate_original('domain_A')
        self.assertEqual(cohort.terminate_original('domain_B'), -int(signal.SIGTERM))
        self.assertIsNone(self.processes[0].poll())
        self.assertEqual(self.events[-2:], [('terminate', 'domain_B'), ('wait', 'domain_B')])
        before = list(self.events)
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            cohort.terminate_original('domain_B')
        self.assertEqual(self.events, before)

    def test_launches_both_originals_before_reading_startups(self):
        cohort = self.fixture()
        cohort.start_originals(); cohort.read_startups()
        self.assertEqual(self.events, [('start', 'domain_A'), ('monitor', 'domain_A'), ('resume', 'domain_A'),
                                       ('start', 'domain_B'), ('monitor', 'domain_B'), ('resume', 'domain_B'),
                                       ('ready', 'domain_A'), ('ready', 'domain_B')])
        self.assertIs(cohort.connection('domain_A'), self.connections[0])

    def test_partial_monitor_failure_retains_both_processes_for_cleanup(self):
        self.fail_monitor = 'domain_B'; cohort = self.fixture()
        with self.assertRaisesRegex(OSError, 'fixture_monitor_failure'): cohort.start_originals()
        with self.assertRaises(ValueError): cohort.start_originals()
        result = cohort.cleanup(0.2)
        self.assertEqual([row['pid'] for row in result['processes']], [100, 101])
        self.assertIn(('close', 'domain_A'), self.events)
        self.assertIn(('close', 'domain_B'), self.events)

    def test_unstarted_process_close_error_does_not_skip_peer_cleanup(self):
        cohort = self.fixture()
        cohort.start_originals(); cohort.read_startups()
        self.processes[0].pid = None
        def broken_close():
            raise OSError('fixture_unstarted_close_failure')
        self.processes[0].close_pipes = broken_close
        result = cohort.cleanup(0.2)
        self.assertEqual(result['errors'], [{'process': 'domain_A', 'stage': 'close', 'exception': 'OSError',
                                            'code': 'fixture_unstarted_close_failure'}])
        self.assertIn(('close', 'domain_B'), self.events)
        self.assertEqual(result['processes'][1]['poll_returncode'], 0)

    def test_startup_failure_consumes_attempt_without_reading_peer(self):
        self.fail_startup = 'domain_A'; cohort = self.fixture(); cohort.start_originals()
        with self.assertRaisesRegex(ValueError, 'fixture_startup_failure'): cohort.read_startups()
        with self.assertRaises(ValueError): cohort.read_startups()
        self.assertNotIn(('ready', 'domain_B'), self.events)
        cohort.cleanup(0.2)
        self.assertIn(('close', 'domain_B'), self.events)

    def test_timeout_kill_precedes_drain_and_cleanup_census(self):
        cohort = self.fixture(); cohort.start_originals(); cohort.read_startups()
        self.connections[0].binding_sha256 = 'fixture-binding'
        self.processes[0].timed_out = True
        result = cohort.cleanup(0.2)
        self.assertEqual([event for event in self.events if event[1] == 'domain_A'][-7:],
                         [('shutdown', 'domain_A'), ('wait', 'domain_A'), ('kill', 'domain_A'), ('wait', 'domain_A'),
                          ('drain', 'domain_A'), ('cleanup', 'domain_A'), ('close', 'domain_A')])
        self.assertEqual(result['processes'][0]['poll_returncode'], -int(signal.SIGKILL))

    def test_failed_drain_and_census_do_not_skip_peer_or_fabricate_row(self):
        self.fail_drain = self.fail_sample = 'domain_A'
        cohort = self.fixture(); cohort.start_originals(); cohort.read_startups()
        result = cohort.cleanup(0.2)
        self.assertEqual([row['stage'] for row in result['errors']], ['drain', 'cleanup_liveness'])
        self.assertEqual(result['liveness'], [{'fixture': 'domain_B', 'checkpoint': 'cleanup'}])
        self.assertIn(('close', 'domain_B'), self.events)

    def test_replacement_requires_original_exit_and_has_no_command_route(self):
        cohort = self.fixture('F07'); cohort.start_originals(); cohort.read_startups()
        original = cohort.connection('domain_A')
        with self.assertRaises(ValueError): cohort.start_replacement()
        self.processes[0].returncode = -9
        replacement = cohort.start_replacement()
        self.assertNotEqual(replacement['launch']['launch_id'], cohort.launch_record('domain_A')['launch_id'])
        self.assertIs(cohort.connection('domain_A'), original)
        with self.assertRaises(ValueError): cohort.connection('replacement')
        with self.assertRaises(ValueError): cohort.start_replacement()
        cohort.cleanup(0.2)
        self.assertNotIn(('shutdown', 'replacement'), self.events)

    def test_unready_and_closed_routes_reject_and_cleanup_does_not_repeat(self):
        cohort = self.fixture()
        with self.assertRaises(ValueError): cohort.connection('domain_A')
        with self.assertRaises(ValueError): cohort.sample('domain_A', 'startup')
        cohort.start_originals(); cohort.read_startups()
        first = cohort.cleanup(0.2); events = list(self.events)
        first['errors'].append({'fixture': 'caller mutation'})
        self.assertEqual(cohort.cleanup(0.2)['errors'], [])
        self.assertEqual(self.events, events)
        with self.assertRaises(ValueError): cohort.connection('domain_A')

    def test_actual_interpreter_exit_and_timeout_cleanup_retain_original_pipes(self):
        observer = MacProcessObserver()
        birth = observer.identity(os.getpid())['macos_birth_tuple']
        binary = observer.paths(os.getpid(), birth)['executable_realpath']
        original_prepare = self.workspace.prepare_launch

        def interpreter_launch(case_id, domain, replacement=False):
            launch = original_prepare(case_id, domain, replacement)
            program = 'import os,time; os.write(1,b\'{"fixture":"ready"}\\n\'); os.write(2,b"fixture stderr\\n"); '
            program += 'os._exit(0)' if domain == 'domain_A' else 'time.sleep(10)'
            launch['argv'] = [binary, '-B', '-c', program]
            return launch

        # Only the executable/argv preparation is replaced. Actual spawn,
        # suspended ownership, monitors, waits, signals and holder checks run.
        # These are explicit interpreter fixtures, never Unreal observations.
        with self.mock.patch.object(self.workspace, 'prepare_launch', side_effect=interpreter_launch):
            cohort = AcquisitionProcessCohort(self.workspace, 'W1', {}, CaptureBudget(1048576))
            self.addCleanup(cohort.trace.close)
            self.addCleanup(cohort.cleanup, 0.2)
            cohort.start_originals()
        for domain in cohort.DOMAINS:
            self.assertEqual(cohort._entries[domain]['monitor'].next_protocol_line(5)[1], b'{"fixture":"ready"}\n')
        cohort._entries['domain_A']['process'].wait(5)
        result = cohort.cleanup(0.2)
        self.assertEqual(result['errors'], [])
        self.assertEqual([row['poll_returncode'] for row in result['processes']], [0, -int(signal.SIGKILL)])
        self.assertEqual([row['kill_sent'] for row in result['processes']], [False, True])
        self.assertEqual(len(result['liveness']), 2)
        for row in result['liveness']:
            self.assertIsNone(row['observed_process'])
            self.assertEqual(len(row['pipe_endpoints']), 3)
            self.assertEqual(row['pipe_endpoints'], row['pipe_holders'])
            self.assertTrue(all(item['pid'] == os.getpid() and item['peer_kernel_id'] is None for item in row['pipe_holders']))
        for domain in cohort.DOMAINS:
            self.assertEqual((self.workspace._output_root / 'W1' / (domain + '.stderr.log')).read_bytes(), b'fixture stderr\n')


class AcquisitionWorkspaceTests(unittest.TestCase):
    """Storage and intercepted audit/build boundaries; no UE compiler runs.

    Component capture tests explicitly replace the still-closed audit method
    together with the compiler. The ordinary direct entrypoint is tested with
    its real denial. Mocked captures confer no audit or build acceptance.
    """

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='city-acquisition-paths-', dir='/private/tmp')
        self.addCleanup(self.temporary.cleanup)
        self.context = Path(self.temporary.name)
        self.runtime = self.context / 'runtime'
        self.output = self.context / 'arbitrary-fresh-artifact-name'
        self.raw = CONTRACT_PATH.read_bytes()
        self.root = CONTRACT_PATH.parent.parent

    def workspace(self):
        return AcquisitionWorkspace(self.raw, self.root, self.runtime, self.output)

    def test_incomplete_normal_acquire_rejects_before_any_build_or_reservation(self):
        from unittest import mock
        import live_cross_domain_evidence_round_trip_harness as harness
        import contextlib
        import io
        stderr = io.StringIO()
        with mock.patch.object(subprocess, 'run') as run, contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as error:
                harness.main(['acquire', '--runtime-parent', str(self.runtime), '--output', str(self.output)])
        self.assertEqual(error.exception.code, 2)
        self.assertIn('lcer.acquisition_implementation_incomplete', stderr.getvalue())
        run.assert_not_called()
        self.assertEqual(list(self.context.iterdir()), [])

    def test_invalid_normal_path_rejects_before_the_compiler_boundary(self):
        from unittest import mock
        import live_cross_domain_evidence_round_trip_harness as harness
        with mock.patch.object(subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, '^lcer.acquisition_path_invalid$'):
                harness.main(['acquire', '--runtime-parent', 'relative', '--output', str(self.output)])
        run.assert_not_called()
        self.assertEqual(list(self.context.iterdir()), [])

    def test_direct_build_rejects_incomplete_audit_before_runtime_log_or_compiler(self):
        from unittest import mock
        import live_cross_domain_evidence_round_trip_harness as harness
        workspace = self.workspace(); workspace.reserve()
        # A forged success record cannot authorize this still-incomplete
        # entrypoint, even when it names the actual candidate source hashes.
        workspace._source_audit = {'returncode': 0, 'source_audit_complete': True,
                                   'files': workspace._source_snapshot, 'unclassified': []}
        with mock.patch.object(harness, 'core_health') as health, \
                mock.patch.object(harness, 'current_python_runtime') as runtime, \
                mock.patch.object(subprocess, 'run') as compiler:
            for _ in range(2):
                with self.assertRaisesRegex(ValueError, '^lcer.acquisition_implementation_incomplete$'):
                    workspace.build_candidate()
        health.assert_not_called()
        runtime.assert_not_called()
        compiler.assert_not_called()
        self.assertEqual(list(self.output.iterdir()), [])
        self.assertFalse(workspace._build_started)
        self.assertIsNone(workspace._build_capture)

    def test_direct_build_rechecks_constraints_and_consumes_an_interrupted_attempt(self):
        from unittest import mock
        workspace = self.workspace()
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            workspace.build_candidate()
        workspace.reserve()
        workspace._plan['constitutional_policy']['build_argv'].append('-Injected')
        with mock.patch.object(subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, '^lcer.obligation_plan_mismatch$'):
                workspace.build_candidate()
        run.assert_not_called()
        self.assertFalse((self.output / 'build.log').exists())
        workspace._plan = FrozenObligationPlanCompiler(self.raw).compile()

        class BoundaryReached(Exception):
            pass

        with mock.patch.object(workspace, '_require_build_source_audit'), \
                mock.patch.object(subprocess, 'run', side_effect=BoundaryReached()) as run:
            with self.assertRaises(BoundaryReached):
                workspace.build_candidate()
            with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
                workspace.build_candidate()
        self.assertEqual(run.call_count, 1)

    def test_nonzero_build_result_retains_actual_log_bytes_without_release_claims(self):
        from unittest import mock
        workspace = self.workspace(); workspace.reserve()
        raw = b'offline compiler-result fixture; no Unreal build\n'

        def failed(argv, **kwargs):
            kwargs['stdout'].write(raw)
            return subprocess.CompletedProcess(argv, 17)

        with mock.patch.object(workspace, '_require_build_source_audit'), \
                mock.patch.object(subprocess, 'run', side_effect=failed):
            with self.assertRaisesRegex(ValueError, '^lcer.build_failed$'):
                workspace.build_candidate()
        log = (self.output / 'build.log').read_bytes()
        python_runtime, compiler = python_runtime_from_build_log(self.raw, log)
        self.assertEqual(compiler, raw)
        self.assertEqual(python_runtime, current_python_runtime())
        self.assertEqual(workspace._build_capture['python_runtime'], python_runtime)
        self.assertEqual(workspace._build_capture['returncode'], 17)
        self.assertEqual(workspace._build_capture['log']['sha256'], hashlib.sha256(log).hexdigest())
        self.assertFalse((self.output / 'build.json').exists())
        self.assertFalse((self.output / 'acquisition.json').exists())

    def test_python_observation_failure_stops_before_the_build_boundary(self):
        from unittest import mock
        import live_cross_domain_evidence_round_trip_harness as harness
        workspace = self.workspace(); workspace.reserve()
        with mock.patch.object(workspace, '_require_build_source_audit'), \
                mock.patch.object(harness, 'current_python_runtime', side_effect=ValueError('fixture_observation_failure')), \
                mock.patch.object(subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, '^fixture_observation_failure$'):
                workspace.build_candidate()
        run.assert_not_called()
        self.assertFalse((self.output / 'build.log').exists())

    def test_runtime_factory_requires_captured_build_before_cache_discovery(self):
        from unittest import mock
        import live_cross_domain_evidence_round_trip_harness as harness
        workspace = self.workspace(); workspace.reserve()
        with mock.patch.object(harness, 'current_dyld_cache') as discover:
            with self.assertRaisesRegex(ValueError, '^lcer.build_capture_missing$'):
                RuntimeBuildInputInventory.from_workspace(workspace)
        discover.assert_not_called()

    def test_changed_python_runtime_after_build_prevents_capture_acceptance(self):
        from unittest import mock
        import live_cross_domain_evidence_round_trip_harness as harness
        workspace = self.workspace(); workspace.reserve()
        before = current_python_runtime()
        after = {**before, 'version': 'changed runtime'}
        with mock.patch.object(workspace, '_require_build_source_audit'), \
                mock.patch.object(harness, 'current_python_runtime', side_effect=[before, after]), \
                mock.patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
            with self.assertRaisesRegex(ValueError, '^lcer.python_runtime_changed$'):
                workspace.build_candidate()
        self.assertEqual(run.call_count, 1)
        self.assertIsNone(workspace._build_capture)
        self.assertFalse((self.output / 'build.json').exists())

    def test_build_inventory_factory_binds_captured_runtime_and_strips_only_prelude(self):
        from unittest import mock
        workspace = self.workspace(); workspace.reserve()
        compiler_log = b'intercepted fixture; no Unreal compiler ran\nResult: Succeeded\n'
        def built(argv, **kwargs):
            kwargs['stdout'].write(compiler_log)
            return subprocess.CompletedProcess(argv, 0)
        with mock.patch.object(workspace, '_require_build_source_audit'), \
                mock.patch.object(subprocess, 'run', side_effect=built):
            capture = workspace.build_candidate()
        calls = []
        def inventory_boundary(instance, *args):
            calls.append(args)
            instance._files, instance._aliases, instance._result = {}, {}, {}
            instance._workspace = instance._capture_raw = instance._invocation_log = None
        with mock.patch.object(BuildActionInputInventory, '__init__', inventory_boundary):
            inventory = BuildActionInputInventory.from_workspace(workspace)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], self.root / 'CityMaterializationProof/Intermediate/Build/Mac/arm64/CityMaterializationProofEditor/Development/Makefile.bin')
        self.assertEqual(calls[0][1], compiler_log)
        self.assertEqual(inventory.snapshot()['python'], capture['python_runtime']['executable'])
        self.assertEqual(inventory.snapshot()['python_runtime'], current_python_runtime())
        workspace._build_capture['python_runtime']['version'] = 'changed runtime'
        with self.assertRaisesRegex(ValueError, '^lcer.build_capture_changed$'):
            inventory.verify()

    def test_rehashed_false_python_version_cannot_enter_build_inventory(self):
        from unittest import mock
        workspace = self.workspace(); workspace.reserve()
        with mock.patch.object(workspace, '_require_build_source_audit'), \
                mock.patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)):
            workspace.build_candidate()
        forged = {**workspace._build_capture['python_runtime'], 'version': 'forged runtime version'}
        raw = b'CITY_LCER_PYTHON ' + stored_json_bytes(forged)
        (self.output / 'build.log').write_bytes(raw)
        workspace._build_capture['python_runtime'] = forged
        workspace._build_capture['log'] = {'path': 'build.log', 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)}
        with mock.patch.object(BuildActionInputInventory, '__init__') as inventory:
            with self.assertRaisesRegex(ValueError, '^lcer.build_capture_changed$'):
                BuildActionInputInventory.from_workspace(workspace)
        inventory.assert_not_called()

    def test_direct_path_rejects_a_changed_execution_copy_before_build(self):
        from unittest import mock
        workspace = self.workspace(); workspace.reserve()
        copy_root = self.context / 'execution-copy'; copy_root.mkdir()
        policy = json.loads(self.raw)
        prefix = policy['runtime']['output_root'] + '/'
        for name in policy['release_members']:
            if not name.startswith(prefix):
                path = copy_root / name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((self.root / name).read_bytes())
        workspace._execution_root = copy_root
        workspace.verify()
        path = copy_root / 'proof_kernel/live_cross_domain_evidence_round_trip.py'
        path.write_bytes(path.read_bytes() + b'\n# changed copy\n')
        with mock.patch.object(subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, '^lcer.dependency_identity_mismatch$'):
                workspace.build_candidate()
        run.assert_not_called()
        self.assertFalse((self.output / 'build.log').exists())

    def test_preflight_has_no_writes_then_reserves_private_distinct_roots(self):
        workspace = self.workspace()
        self.assertEqual(list(self.context.iterdir()), [])
        workspace.reserve()
        workspace.begin_case('W1')
        a = workspace.prepare_launch('W1', 'domain_A')
        b = workspace.prepare_launch('W1', 'domain_B')
        self.assertEqual(len(a['argv']), 13)
        self.assertNotEqual(a['launch_id'], b['launch_id'])
        self.assertNotEqual(a['process_root_realpath'], b['process_root_realpath'])
        self.assertEqual(a['cwd'], '/Users/boandersson/Projects/CITY')
        for plan in (a, b):
            directory = Path(plan['process_root_realpath'])
            self.assertEqual(sorted(path.name for path in directory.iterdir()), ['home', 'tmp', 'user'])
            self.assertEqual(plan['environment']['HOME'], str(directory / 'home'))
            self.assertEqual(plan['environment']['TMPDIR'], str(directory / 'tmp'))
            self.assertEqual(plan['argv'][-1], '-UserDir=' + str(directory / 'user'))
        for path in [self.runtime, self.output, *self.runtime.rglob('*'), *self.output.rglob('*')]:
            self.assertEqual(path.stat().st_mode & 0o777, 0o700)
        workspace.verify()

    def test_reused_paths_case_and_launch_are_rejected_without_overwrite(self):
        workspace = self.workspace(); workspace.reserve(); workspace.begin_case('W1')
        workspace.prepare_launch('W1', 'domain_A')
        marker = self.output / 'retained.bin'; marker.write_bytes(b'retain me')
        for action in (workspace.reserve, lambda: workspace.begin_case('W1'),
                       lambda: workspace.prepare_launch('W1', 'domain_A')):
            with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
                action()
        with self.assertRaisesRegex(ValueError, '^lcer.acquisition_path_invalid$'):
            self.workspace()
        self.assertEqual(marker.read_bytes(), b'retain me')

    def test_unreserved_unknown_and_illegal_replacement_launches_reject(self):
        workspace = self.workspace()
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            workspace.begin_case('W1')
        workspace.reserve(); workspace.begin_case('W1'); workspace.begin_case('F07')
        for args in (('W1', 'domain_A', True), ('F07', 'domain_B', True), ('F07', 'domain_A', True),
                     ('not_a_case', 'domain_A', False), ('W1', 'domain_C', False)):
            with self.subTest(args=args):
                with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
                    workspace.prepare_launch(*args)
        original = workspace.prepare_launch('F07', 'domain_A')
        replacement = workspace.prepare_launch('F07', 'domain_A', True)
        self.assertNotEqual(original['launch_id'], replacement['launch_id'])
        self.assertEqual(Path(replacement['process_root_realpath']).name, 'replacement')
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            workspace.prepare_launch('F07', 'domain_A', True)

    def test_changed_policy_and_replaced_private_directory_block_next_case(self):
        workspace = self.workspace(); workspace.reserve()
        workspace._plan['constitutional_policy']['launch_argv'].append('-Injected')
        with self.assertRaisesRegex(ValueError, '^lcer.obligation_plan_mismatch$'):
            workspace.begin_case('W1')
        workspace._plan = FrozenObligationPlanCompiler(self.raw).compile()
        retained = self.context / 'retained-runtime'; self.runtime.rename(retained)
        self.runtime.mkdir(mode=0o700)
        with self.assertRaisesRegex(ValueError, '^lcer.acquisition_directory_changed$'):
            workspace.begin_case('W1')
        self.assertTrue(retained.is_dir())

    def test_alias_overlap_and_other_repository_are_rejected_before_writes(self):
        alias = self.context / 'alias'; alias.symlink_to(self.context, target_is_directory=True)
        for runtime, output in ((Path('relative'), self.output), (alias / 'runtime', self.output),
                                (self.runtime, self.runtime), (self.runtime, self.root / 'unlisted-output')):
            with self.subTest(runtime=str(runtime), output=str(output)):
                with self.assertRaisesRegex(ValueError, '^lcer.acquisition_path_invalid$'):
                    AcquisitionWorkspace(self.raw, self.root, runtime, output)
        with self.assertRaisesRegex(ValueError, '^lcer.acquisition_repository_invalid$'):
            AcquisitionWorkspace(self.raw, self.context, self.runtime, self.output)
        self.assertEqual(list(self.context.iterdir()), [alias])


class ObservedBuildRecordTests(unittest.TestCase):
    """Metadata/capture fixtures joined to real file bytes, never a UE build.

    The fixture binds the metadata reader manually. Production obtains that
    binding only from BuildActionInputInventory.from_workspace. Source-audit
    fixture rows prove record binding here, not independent audit acceptance.
    """

    def setUp(self):
        package = AcquisitionPackageWriterTests()
        package.setUp()
        self.addCleanup(package.doCleanups)
        package.build_record()
        self.package, self.writer, self.workspace = package, package.writer, package.workspace
        metadata = RuntimeBuildInputInventoryTests()
        metadata.setUp()
        self.addCleanup(metadata.doCleanups)
        self.metadata = metadata
        runtime = package.policy['runtime']
        build = metadata.build
        build._result.update(editor=build._pin(runtime['engine']),
                             project=build._pin(CONTRACT_PATH.parent.parent / runtime['project']),
                             python=metadata.python['executable'], python_runtime=metadata.python)
        self.workspace._build_capture.update(source_files=dict(self.workspace._source_snapshot),
                                             python_runtime=metadata.python)
        build._workspace = self.workspace
        build._capture_raw = stored_json_bytes(self.workspace._build_capture)
        build._invocation_log = external_file_identity(package.artifacts / 'build.log')
        self.inventory = RuntimeBuildInputInventory(package.raw, build, metadata.cache_path,
                                                    metadata.python, metadata.fixture.module)
        row = copy.deepcopy(metadata.row)
        row.update(cwd_realpath=str(CONTRACT_PATH.parent.parent), executable=build.snapshot()['editor'])
        row['startup']['cwd_realpath'] = row['cwd_realpath']
        images = [image for image in macho_file_images(runtime['engine']) if image['architecture'] == 'arm64']
        images += macho_file_images(metadata.fixture.module) + self.inventory.cache['images']
        row['loaded_images'] = sorted(images, key=lambda image: image['realpath'])
        row['startup']['loaded_images'] = copy.deepcopy(row['loaded_images'])
        cases = set(package.policy['artifact_hash_graph']['case_ids'])
        expected = {(case, domain, False) for case in cases for domain in ('domain_A', 'domain_B')}
        expected.add(('F07', 'domain_A', True))
        self.workspace._cases = cases
        self.workspace._launches = expected
        self.launches = []
        self.workspace.verify()
        # These are simulated observations of immutable test files. Check
        # the source snapshot before/after fixture setup; avoid hundreds of
        # repeated source scans while populating it. All native file, image,
        # cache and observation checks still execute. Production assembly
        # below runs with the actual workspace verifier restored.
        with mock.patch.object(self.workspace, 'verify'):
            for index, (case, domain, _) in enumerate(sorted(expected)):
                launch = {'witness_id': case, 'domain': domain, 'launch_id': 'fixture-%d' % index}
                row['pid'] = 1000 + index
                row['startup'].update(launch, pid=row['pid'])
                self.inventory.validate_observation(row)
                self.launches.append(launch)
        self.workspace.verify()
        self.workspace._launch_ids = {row['launch_id'] for row in self.launches}
        names = set(package.policy['planned_source_paths']) | {
            name for group in ('predecessors', 'unchanged_dependencies') for name in package.policy[group]
            if name.endswith('.py')}
        self.audit = {'files': [], 'edges': [{'path': 'proof_kernel/live_cross_domain_evidence_round_trip_harness.py',
                       'function': 'metadata_fixture', 'input': 'platform', 'callee': 'metadata_fixture', 'consequence': 'provenance'}],
                      'rejected_mutations': list(package.policy['process_input_contract']['source_negative_cases']),
                      'argv': ['metadata-fixture-only'], 'returncode': 0}
        for name in sorted(names):
            raw = (CONTRACT_PATH.parent.parent / name).read_bytes()
            self.audit['files'].append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)})

    def assemble(self, inventory=None, audit=None, launches=None):
        return self.writer.observed_build_record(self.inventory if inventory is None else inventory,
                                                self.audit if audit is None else audit,
                                                self.launches if launches is None else launches)

    def test_complete_record_joins_capture_files_and_all_launches_then_writes(self):
        self.assertFalse(isinstance(self.workspace.verify, mock.Mock))
        record = self.assemble()
        self.assertEqual(set(record), set(self.package.policy['wire_schemas']['build_record']['required']))
        for key in ('argv', 'cwd', 'started_at', 'finished_at', 'returncode', 'log'):
            self.assertEqual(record[key], self.workspace._build_capture[key])
        for key, value in self.writer.source_identity.items():
            self.assertEqual(record[key], value)
        self.assertEqual(record['external_inputs'], self.inventory.external_inputs())
        self.assertEqual(record['modules'], self.metadata.build.snapshot()['modules'])
        self.assertEqual(record['source_audit'], self.audit)
        self.assertEqual(len(self.launches), 71)
        self.assertFalse((self.package.artifacts / 'build.json').exists())
        result = self.writer.write_build(record)
        raw = (self.package.artifacts / 'build.json').read_bytes()
        self.assertEqual(parse_stored_json(raw), record)
        self.assertEqual(result['sha256'], hashlib.sha256(raw).hexdigest())
        record['source_audit']['files'].clear()
        record['external_inputs']['loaded_images'].clear()
        self.assertTrue(self.audit['files'])
        self.assertTrue(self.inventory.external_inputs()['loaded_images'])

    def test_unbound_or_wrong_owner_metadata_cannot_produce_build_record(self):
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_build_capture_missing$'):
            self.assemble(inventory=object())
        self.metadata.build._workspace = None
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_build_capture_missing$'):
            self.assemble()
        self.assertFalse((self.package.artifacts / 'build.json').exists())

    def test_missing_failed_or_changed_capture_rejects(self):
        original = copy.deepcopy(self.workspace._build_capture)
        for defect, code in [('missing', 'lcer.build_capture_missing'), ('failed', 'lcer.build_capture_missing'),
                             ('changed', 'lcer.build_capture_changed')]:
            with self.subTest(defect=defect):
                captured = copy.deepcopy(original)
                if defect == 'missing':
                    captured = None
                elif defect == 'failed':
                    captured['returncode'] = 1
                else:
                    captured['finished_at'] = 'changed'
                self.workspace._build_capture = captured
                with self.assertRaisesRegex(ValueError, '^' + code + '$'):
                    self.assemble()
        self.workspace._build_capture = original

    def test_launch_subset_duplicates_and_owner_inventory_mismatch_reject(self):
        cases = [self.launches[:-1], [*self.launches[:-1], self.launches[0]]]
        wrong = copy.deepcopy(self.launches)
        wrong[0]['launch_id'] = 'not-owner-created'
        cases.append(wrong)
        wrong = copy.deepcopy(self.launches)
        wrong[0]['extra'] = True
        cases.append(wrong)
        wrong = copy.deepcopy(self.launches)
        wrong[0]['domain'] = 'domain_B'
        cases.append(wrong)
        for launches in cases:
            with self.subTest(launches=launches[:1]), self.assertRaisesRegex(ValueError, '^lcer.runtime_input_launches_incomplete$'):
                self.assemble(launches=launches)
        removed = self.inventory._launches.pop(self.launches[0]['launch_id'])
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_launches_incomplete$'):
            self.assemble()
        self.inventory._launches[self.launches[0]['launch_id']] = removed
        self.workspace._launches.remove(('F07', 'domain_A', True))
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_launches_incomplete$'):
            self.assemble()

    def test_audit_members_edges_and_negative_case_inventory_are_bound(self):
        for defect in ('missing_file', 'duplicate_file', 'unlisted_file', 'unknown_edge', 'missing_attack', 'duplicate_attack', 'empty_argv', 'empty_edges', 'failed'):
            audit = copy.deepcopy(self.audit)
            if defect == 'missing_file':
                audit['files'].pop()
            elif defect == 'duplicate_file':
                audit['files'].append(audit['files'][0])
            elif defect == 'unlisted_file':
                audit['files'].append({'path': 'unlisted.py', 'sha256': '0' * 64, 'size_bytes': 0})
            elif defect == 'unknown_edge':
                audit['edges'][0]['path'] = 'unlisted.py'
            elif defect == 'missing_attack':
                audit['rejected_mutations'].pop()
            elif defect == 'duplicate_attack':
                audit['rejected_mutations'][-1] = audit['rejected_mutations'][0]
            elif defect == 'empty_argv':
                audit['argv'] = []
            elif defect == 'empty_edges':
                audit['edges'] = []
            else:
                audit['returncode'] = 1
            with self.subTest(defect=defect), self.assertRaisesRegex(ValueError, '^lcer.source_audit_record_invalid$'):
                self.assemble(audit=audit)
        audit = copy.deepcopy(self.audit)
        audit['source_audit_complete'] = True
        with self.assertRaisesRegex(ValueError, '^lcer.schema_invalid$'):
            self.assemble(audit=audit)

    def test_audit_hash_and_size_must_match_actual_source(self):
        for field, value in [('sha256', '0' * 64), ('size_bytes', 0)]:
            audit = copy.deepcopy(self.audit)
            audit['files'][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, '^lcer.source_audit_record_changed$'):
                self.assemble(audit=audit)

    def test_restored_native_bytes_do_not_reopen_failed_inventory(self):
        raw = self.metadata.config.read_bytes()
        self.metadata.config.write_bytes(raw + b'Changed=True\n')
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
            self.assemble()
        self.metadata.config.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, '^lcer.runtime_input_inventory_failed$'):
            self.assemble()
        self.assertFalse((self.package.artifacts / 'build.json').exists())

    def test_assembled_audit_record_cannot_open_the_real_build_guard(self):
        record = self.assemble()
        self.workspace._source_audit = record['source_audit']
        with mock.patch('live_cross_domain_evidence_round_trip_harness.subprocess.run') as compiler:
            with self.assertRaisesRegex(ValueError, '^lcer.acquisition_implementation_incomplete$'):
                self.workspace.build_candidate()
        compiler.assert_not_called()
        self.assertFalse(self.workspace._build_started)


class AcquisitionPackageWriterTests(unittest.TestCase):
    """Closed byte-graph fixtures; no compiler, Unreal or live proof."""

    def setUp(self):
        self.raw = CONTRACT_PATH.read_bytes()
        self.policy = json.loads(self.raw)
        self.temporary = tempfile.TemporaryDirectory(prefix='city-package-writer-', dir='/private/tmp')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.release = self.root / 'release'
        self.release.mkdir()
        self.artifacts = self.root / 'arbitrary-artifact-name'
        prefix = self.policy['runtime']['output_root'] + '/'
        for name in self.policy['release_members']:
            if name.startswith(prefix):
                continue
            path = self.release / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((CONTRACT_PATH.parent.parent / name).read_bytes())
        self.workspace = AcquisitionWorkspace(self.raw, CONTRACT_PATH.parent.parent, self.root / 'runtime', self.artifacts)
        self.workspace._execution_root = self.release
        self.workspace.reserve()
        self.writer = AcquisitionPackageWriter(self.workspace, CaptureBudget(64 * 1024 * 1024))

    def build_record(self):
        self.writer.write_references()
        (self.artifacts / 'build.log').write_bytes(b'intercepted-build byte fixture; no compiler ran\n')
        captured = {'argv': [value.format(absolute_city_project=str(CONTRACT_PATH.parent.parent / self.policy['runtime']['project']))
                             for value in self.policy['build_argv']], 'cwd': str(CONTRACT_PATH.parent.parent),
                    'returncode': 0, 'started_at': 'fixture-start', 'finished_at': 'fixture-finish',
                    'log': self.writer._artifact('build.log')}
        self.workspace._build_capture = captured
        record = schema_example(self.policy['wire_schemas']['build_record'], self.policy['wire_schemas'])
        record.update(captured, **self.writer.source_identity)
        record['editor']['realpath'] = self.policy['runtime']['engine']
        record['project'] = external_file_identity(CONTRACT_PATH.parent.parent / self.policy['runtime']['project'])
        return record

    def prepare(self):
        self.writer.write_build(self.build_record())
        for name in self.policy['artifact_relative_paths']:
            if name == 'acquisition.json' or (self.artifacts / name).exists():
                continue
            path = self.artifacts / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'byte graph fixture; not process evidence\n')
        references = {symbol: (self.artifacts / 'canonical' / (symbol + '.json')).read_text() for symbol in ('R0', 'R1')}
        for name in self.policy['artifact_hash_graph']['case_ids']:
            plan = select_frozen_case(self.raw, name)
            record = schema_example(self.policy['wire_schemas']['case_record'], self.policy['wire_schemas'])
            record.update(witness_id=name, status='accepted' if plan['kind'] == 'witness' else 'expected_failure')
            record['failure_codes'] = ([] if plan['kind'] == 'witness' else [plan['failure_family']['failure_code']]
                                       if plan['kind'] == 'failure' else [plan['underlying_code']])
            record['canonical_artifacts'] = {'initial_raw_utf8': references['R0'],
                                            'published_raw_utf8': references['R1'] if plan['publication_count'] else None,
                                            'terminal_raw_utf8': references[plan['terminal_canonical']]}
            record['claims'].update(canonical_commit=bool(plan['publication_count']), synchronized_representation=plan['kind'] == 'witness')
            record['artifact_sha256'] = [self.writer._artifact(path) for path in self.policy['artifact_hash_graph']['case_record_targets'][name]]
            (self.artifacts / name / 'record.json').write_bytes(stored_json_bytes(record))

    def byte_context(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        return verifier.authenticate_release(self.release, self.artifacts)

    def test_exact_package_graph_and_cold_cli_does_not_claim_live_acceptance(self):
        self.prepare()
        result = self.writer.finalize()
        self.assertEqual((result['artifact_count'], result['release_member_count']), (219, 289))
        self.assertFalse(result['live_acceptance_verified'])
        context = self.byte_context()
        self.assertEqual(len(context['source_bytes']), 70)
        self.assertNotIn('accepted', context)
        acquisition = parse_stored_json(context['artifacts']['acquisition.json'])
        self.assertEqual(acquisition['source_commit'], self.writer.source_identity['source_commit'])
        self.assertEqual(acquisition['artifact_members'], self.policy['artifact_relative_paths'])
        self.assertEqual([row['path'] for row in acquisition['artifact_hashes']], self.policy['artifact_hash_graph']['acquisition_targets'])
        self.assertNotIn('acquisition.json', [row['path'] for row in acquisition['artifact_hashes']])
        manifest = (self.release / self.policy['release_manifest']).read_bytes()
        self.assertNotIn(self.policy['release_manifest'].encode(), manifest)
        invoked = subprocess.run([sys.executable, '-B', 'proof_kernel/verify_live_cross_domain_evidence_round_trip_release.py',
                                  'verify', '--artifacts', str(self.artifacts)], cwd=self.release, capture_output=True, timeout=30)
        self.assertEqual(invoked.returncode, 2)
        self.assertEqual(json.loads(invoked.stdout)['status'], 'fail')
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            self.writer.finalize()
        self.assertEqual((self.release / self.policy['release_manifest']).read_bytes(), manifest)

    def test_extra_member_blocks_before_acquisition_and_manifest_writes(self):
        self.prepare()
        (self.artifacts / 'extra.bin').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError, '^lcer.acquisition_artifact_membership_invalid$'):
            self.writer.finalize()
        self.assertFalse((self.artifacts / 'acquisition.json').exists())
        self.assertFalse((self.release / self.policy['release_manifest']).exists())
        self.assertEqual((self.artifacts / 'extra.bin').read_bytes(), b'extra')

    def test_changed_stream_cannot_keep_the_old_case_hash(self):
        self.prepare()
        path = self.artifacts / 'W1/domain_A.stdout.log'
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, '^lcer.case_artifact_graph_invalid$'):
            self.writer.finalize()
        self.assertFalse((self.artifacts / 'acquisition.json').exists())

    def test_reference_change_cannot_be_rehashed_into_a_new_package(self):
        self.prepare()
        path = self.artifacts / 'canonical/R0.json'
        path.write_bytes(path.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError, '^lcer.artifact_changed_after_write$'):
            self.writer.finalize()

    def test_changed_build_argv_rejects_before_build_record_write(self):
        record = self.build_record()
        record['argv'] = record['argv'] + ['-Injected']
        with self.assertRaisesRegex(ValueError, '^lcer.build_record_invalid$'):
            self.writer.write_build(record)
        self.assertFalse((self.artifacts / 'build.json').exists())
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            self.writer.write_build(record)

    def test_changed_release_source_rejects_without_overwriting_it(self):
        self.prepare()
        path = self.release / 'proof_kernel/live_cross_domain_evidence_round_trip_harness.py'
        changed = path.read_bytes() + b'\n# changed copied source\n'
        path.write_bytes(changed)
        with self.assertRaisesRegex(ValueError, '^lcer.dependency_identity_mismatch$'):
            self.writer.finalize()
        self.assertEqual(path.read_bytes(), changed)
        self.assertFalse((self.artifacts / 'acquisition.json').exists())

    def test_failed_case_retains_a_closed_failed_package(self):
        self.prepare()
        path = self.artifacts / 'W1/record.json'
        record = parse_stored_json(path.read_bytes())
        record.update(status='acquisition_failure', failure_codes=['fixture_acquisition_failure'])
        record['claims']['synchronized_representation'] = False
        path.write_bytes(stored_json_bytes(record))
        result = self.writer.finalize()
        self.assertTrue(result['byte_graph_complete'])
        acquisition = parse_stored_json(self.byte_context()['artifacts']['acquisition.json'])
        self.assertEqual(acquisition['status'], 'failed')
        self.assertEqual(set(acquisition['claims'].values()), {False})

    def test_wrong_normalized_failure_code_cannot_be_packaged(self):
        self.prepare()
        path = self.artifacts / 'F03/record.json'
        record = parse_stored_json(path.read_bytes())
        record['failure_codes'] = ['LCER_INPUT_SET_INVALID']
        path.write_bytes(stored_json_bytes(record))
        with self.assertRaisesRegex(ValueError, '^lcer.case_status_invalid$'):
            self.writer.finalize()


class ProjectSourcePreflightTests(unittest.TestCase):
    """Temporary source-inventory fixtures confer no executable or live proof."""

    def setUp(self):
        self.raw = CONTRACT_PATH.read_bytes()
        self.policy = json.loads(self.raw)
        self.temporary = tempfile.TemporaryDirectory(prefix="city-source-preflight-", dir="/private/tmp")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        preserved = {**self.policy["predecessors"], **self.policy["canonical_records"],
                     **self.policy["unchanged_dependencies"]}
        preserved_names = [*preserved, "proof_kernel/live_cross_domain_evidence_round_trip_contract.json",
                           "Live Cross-Domain Evidence Round-Trip Proof - Draft.md"]
        for name in preserved_names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((CONTRACT_PATH.parent.parent / name).read_bytes())
        for name in self.policy["planned_source_paths"]:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"inventory fixture only\n")
        self.descriptor = self.root / self.policy["runtime"]["plugin"] / "CityLiveEvidenceProof.uplugin"
        self.descriptor.write_bytes(stored_json_bytes({
            "FileVersion": 3, "EnabledByDefault": True, "CanContainContent": False,
            "Modules": [{"Name": "CityLiveEvidenceProof", "Type": "Runtime", "LoadingPhase": "Default"}],
        }))

    def test_complete_source_inventory_from_actual_file_bytes(self):
        result = inspect_project_sources(self.raw, self.root)
        self.assertEqual(len(result["preserved_files"]), 61)
        self.assertEqual(len(result["candidate_files"]), 11)
        for row in result["preserved_files"] + result["candidate_files"]:
            raw = (self.root / row["path"]).read_bytes()
            self.assertEqual(row["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(row["size_bytes"], len(raw))
        self.assertEqual({r["path"] for r in result["candidate_files"]}, set(self.policy["planned_source_paths"]))

    def test_missing_candidate_or_changed_preserved_file_rejects(self):
        path = self.root / self.policy["planned_source_paths"][-1]
        original = path.read_bytes(); path.unlink()
        with self.assertRaisesRegex(ValueError, "^lcer.dependency_identity_mismatch$"):
            inspect_project_sources(self.raw, self.root)
        path.write_bytes(original)
        path = self.root / "CityMaterializationProof/Config/DefaultEngine.ini"
        path.write_bytes(path.read_bytes() + b"\nchanged\n")
        with self.assertRaisesRegex(ValueError, "^lcer.dependency_identity_mismatch$"):
            inspect_project_sources(self.raw, self.root)

    def test_unlisted_project_source_config_or_plugin_rejects(self):
        for name in ["CityMaterializationProof/Source/Injected.cpp", "CityMaterializationProof/Config/Injected.ini",
                     "CityMaterializationProof/Plugins/Injected/Injected.uplugin"]:
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b"injected\n")
            with self.subTest(path=name):
                with self.assertRaisesRegex(ValueError, "^lcer.source_input_forbidden$"):
                    inspect_project_sources(self.raw, self.root)
            path.unlink()

    def test_only_declared_plugin_build_outputs_are_excluded_from_source(self):
        path = self.descriptor.parent / "Intermediate/Build/object.o"
        path.parent.mkdir(parents=True); path.write_bytes(b"generated fixture\n")
        result = inspect_project_sources(self.raw, self.root)
        self.assertNotIn(path.relative_to(self.root).as_posix(), result["project_source_paths"])
        forbidden = self.root / "CityMaterializationProof/Plugins/Injected/Intermediate/object.o"
        forbidden.parent.mkdir(parents=True); forbidden.write_bytes(b"undeclared plugin\n")
        with self.assertRaisesRegex(ValueError, "^lcer.source_input_forbidden$"):
            inspect_project_sources(self.raw, self.root)

    def test_descriptor_cannot_enable_another_plugin_or_change_module(self):
        original = self.descriptor.read_bytes()
        for key, value in [("Plugins", [{"Name": "Injected", "Enabled": True}]),
                           ("EnabledByDefault", False), ("CanContainContent", True),
                           ("Modules", [{"Name": "Injected", "Type": "Runtime", "LoadingPhase": "Default"}])]:
            changed = json.loads(original); changed[key] = value
            self.descriptor.write_bytes(stored_json_bytes(changed))
            with self.subTest(field=key):
                with self.assertRaisesRegex(ValueError, "^lcer.source_input_forbidden$"):
                    inspect_project_sources(self.raw, self.root)
        self.descriptor.write_bytes(original)

    def test_stdlib_shadow_file_and_package_reject(self):
        shadow = self.root / "proof_kernel/json.py"; shadow.write_bytes(b"raise RuntimeError('must not execute')\n")
        with self.assertRaisesRegex(ValueError, "^lcer.source_input_forbidden$"):
            inspect_project_sources(self.raw, self.root)
        shadow.unlink(); package = self.root / "proof_kernel/json"; package.mkdir()
        with self.assertRaisesRegex(ValueError, "^lcer.source_input_forbidden$"):
            inspect_project_sources(self.raw, self.root)

    def test_source_alias_and_escape_reject(self):
        target = self.root / "CityMaterializationProof/Config/DefaultEngine.ini"
        alias = self.root / "CityMaterializationProof/Config/Alias.ini"; alias.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "^lcer.dependency_path_invalid$"):
            inspect_project_sources(self.raw, self.root)
        for path in ["../outside", str(target), "CityMaterializationProof/Config/Alias.ini"]:
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, "^lcer.dependency_path_invalid$"):
                    source_file_bytes(self.root, path)


class BuildRuleSourceInventoryTests(unittest.TestCase):
    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.reader = verifier.BuildRuleSourceInventory()
        self.path = ('CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/'
                     'CityLiveEvidenceProof/CityLiveEvidenceProof.Build.cs')
        self.raw = (Path(__file__).resolve().parents[1] / self.path).read_bytes()

    def test_actual_build_rule_constructor_calls_and_store_are_enumerated(self):
        result = self.reader.parse(self.path, self.raw)
        self.assertEqual(len(result['functions']), 1)
        function = result['functions'][0]
        self.assertEqual(function['function'], 'CityLiveEvidenceProof.CityLiveEvidenceProof')
        self.assertEqual(function['parameters'], [{'name': 'Target', 'type': 'ReadOnlyTargetRules'}])
        self.assertEqual([c['callee'] for c in result['calls']],
                         ['base', 'PublicDependencyModuleNames.AddRange', 'PrivateDependencyModuleNames.AddRange',
                          'AddEngineThirdPartyPrivateStaticDependencies'])
        self.assertEqual([v['value'] for v in result['calls'][1]['arguments'][0]['items']],
                         ['Core', 'CoreUObject', 'Engine'])
        self.assertEqual(result['stores'][0]['target']['value'], 'PCHUsage')
        self.assertEqual(result['stores'][0]['value']['value'], 'PCHUsageMode.UseExplicitOrSharedPCHs')
        self.assertFalse(result['source_audit_complete'])

    def test_comments_and_literal_source_text_do_not_create_call_sites(self):
        raw = b'// System.Environment.GetEnvironmentVariable("ignored");\n' + self.raw
        raw = raw.replace(b'"Core"', b'"not_code() /* literal */"')
        result = self.reader.parse(self.path, raw)
        self.assertEqual(len(result['calls']), 4)
        self.assertEqual(result['calls'][1]['arguments'][0]['items'][0]['value'], 'not_code() /* literal */')
        self.assertEqual(result['functions'][0]['line'], 6)

    def test_nested_external_input_call_is_preserved_in_its_store(self):
        raw = self.raw.replace(b'PCHUsageMode.UseExplicitOrSharedPCHs',
                               b'Choose(System.Environment.GetEnvironmentVariable("OWNER"))')
        result = self.reader.parse(self.path, raw)
        call = next(c for c in result['calls'] if c['callee'] == 'System.Environment.GetEnvironmentVariable')
        self.assertEqual(call['arguments'][0]['value'], 'OWNER')
        self.assertEqual(call['function'], 'CityLiveEvidenceProof.CityLiveEvidenceProof')
        self.assertIs(result['stores'][0]['value']['arguments'][0], call)
        self.assertFalse(result['source_audit_complete'])

    def test_unsupported_extra_method_or_initializer_rejects_entire_inventory(self):
        for tail in (b'public void Extra() { System.Console.WriteLine("side effect"); }\n',
                     b'public string Extra = System.Environment.GetEnvironmentVariable("OWNER");\n'):
            raw = self.raw.rstrip()[:-1] + tail + b'}\n'
            with self.subTest(tail=tail), self.assertRaisesRegex(ValueError, '^lcer.build_rule_syntax_unclassified$'):
                self.reader.parse(self.path, raw)

    def test_preprocessor_and_unhandled_string_forms_are_never_skipped(self):
        for raw in (b'#if false\n' + self.raw + b'#endif\n',
                    self.raw.replace(b'"Core"', b'@"Core"'),
                    self.raw.replace(b'"Core"', b'"\\u0043ore"'),
                    self.raw + b'/* unterminated', self.raw + b'\x00'):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, '^lcer.build_rule_syntax_unclassified$'):
                self.reader.parse(self.path, raw)

    def test_extra_class_and_import_alias_are_not_ignored(self):
        for raw in (self.raw + b'public class Hidden {}\n',
                    self.raw.replace(b'using UnrealBuildTool;', b'using ModuleRules = Hidden.ModuleRules;')):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, '^lcer.build_rule_syntax_unclassified$'):
                self.reader.parse(self.path, raw)


class BuildRuleEffectAnalysisTests(unittest.TestCase):
    """Source-only effects; no rule constructor or build tool executes."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.analysis = verifier.BuildRuleEffectAnalysis()
        self.path = ('CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/'
                     'CityLiveEvidenceProof/CityLiveEvidenceProof.Build.cs')
        self.raw = (Path(__file__).resolve().parents[1] / self.path).read_bytes()
        engine = Path('/Users/Shared/Epic Games/UE_5.8/Engine/Source/Programs/UnrealBuildTool/Configuration/Rules')
        self.engine = {name: (engine / name).read_bytes() for name in self.analysis.ENGINE_SOURCES}

    def analyze(self, raw=None):
        return self.analysis.analyze(self.path, self.raw if raw is None else raw, self.engine)

    def test_actual_constructor_effects_bind_exact_arguments_and_backing_fields(self):
        result = self.analyze()
        effects = result['effects']
        self.assertEqual([e['operation'] for e in effects], ['construct_base', 'store', 'append', 'append', 'append'])
        self.assertEqual(effects[0]['arguments'][0], {'type': 'UnrealBuildTool.ReadOnlyTargetRules',
                         'reference': 'target', 'origins': ['platform:target']})
        self.assertEqual(effects[1]['target'], 'receiver.PCHUsagePrivate')
        self.assertEqual(effects[1]['value']['value'], 'PCHUsageMode.UseExplicitOrSharedPCHs')
        self.assertEqual(effects[2]['receiver'], 'receiver.PublicDependencyModuleNames')
        self.assertEqual(effects[3]['receiver'], 'receiver.PrivateDependencyModuleNames')
        self.assertEqual([[e['value'] for e in effect['elements']] for effect in effects[2:]],
                         [['Core', 'CoreUObject', 'Engine'], ['Json', 'Projects'], ['OpenSSL']])
        self.assertTrue(all(e['element_transfer'] == 'ordered_reference_copy' and
                            e['argument_container_retained'] is False for e in effects[2:]))
        self.assertEqual(result['unclassified'], [])
        self.assertEqual(len(result['source_edges']), 2)
        self.assertEqual({e['callee'] for e in result['source_edges']}, {self.analysis.BASE, self.analysis.THIRD_PARTY})
        self.assertTrue(all(set(e) == {'path', 'function', 'input', 'callee', 'consequence'} and
                            e['input'] == 'platform' and e['consequence'] == 'provenance' for e in result['source_edges']))
        self.assertTrue(result['external_obligations'])
        self.assertFalse(result['source_audit_complete'])

    def test_base_reads_current_checker_content_and_retains_deferred_aliases(self):
        effects = self.analyze()['effects'][0]['operations']
        clone = next(e for e in effects if e['operation'] == 'conditional_clone')
        self.assertEqual(clone['source'], 'ModuleRules.DefaultStaticAnalyzerDisabledCheckers')
        self.assertEqual(clone['guard'], {'op': 'not_equal', 'left': 'target.StaticAnalyzer', 'right': 'StaticAnalyzer.None'})
        self.assertEqual(clone['elements'], 'current_string_references')
        warnings = next(e for e in effects if e['operation'] == 'construct_warnings')
        self.assertEqual(warnings['retained_aliases'], {'context.module': 'receiver', 'provider.module': 'receiver',
                         'context.target': None, 'parent_warnings': 'target.CppCompileWarningSettings', 'logger': 'target.Logger'})
        self.assertEqual(warnings['invoked_callbacks'], [])
        self.assertFalse(warnings['applies_defaults'])
        self.assertIn('UnrealBuildTool.ModuleRules,', warnings['signature'])

    def test_precompiled_guard_is_not_replaced_by_a_default_value(self):
        effect = self.analyze()['effects'][-1]
        self.assertEqual(effect['guard'], {'op': 'short_circuit_or',
                         'left': {'op': 'not', 'value': 'receiver.bUsePrecompiled'},
                         'right': {'op': 'equal', 'left': 'target.LinkType', 'right': 'TargetLinkType.Monolithic'}})
        self.assertIn('platform:receiver.bUsePrecompiled', effect['origins'])
        self.assertIn('platform:target', effect['origins'])

    def test_parameter_renaming_preserves_the_same_target_alias(self):
        raw = self.raw.replace(b' Target)', b' Context)').replace(b'base(Target)', b'base(Context)')
        raw = raw.replace(b'Dependencies(Target,', b'Dependencies(Context,')
        result = self.analyze(raw)
        self.assertEqual(result['functions'][0]['parameters'][0]['name'], 'Context')
        self.assertEqual(result['effects'][0]['arguments'], result['effects'][-1]['arguments'][:1])
        self.assertEqual(result['unclassified'], [])

    def test_nested_environment_read_is_retained_at_its_effect_destination(self):
        for before, after in ((b'PCHUsageMode.UseExplicitOrSharedPCHs', b'System.Environment.GetEnvironmentVariable("OWNER")'),
                              (b'"Core"', b'System.Environment.GetEnvironmentVariable("OWNER")')):
            with self.subTest(before=before):
                result = self.analyze(self.raw.replace(before, after))
                edge = next(e for e in result['unclassified'] if e['callee'] == 'System.Environment.GetEnvironmentVariable')
                self.assertEqual(edge['path'], self.path)
                self.assertEqual(edge['function'], 'CityLiveEvidenceProof.CityLiveEvidenceProof')
                self.assertIn(edge['line'], (7, 8))
                destination = next(e for e in result['effects'] if e['line'] == edge['line'])
                self.assertIn('unclassified:System.Environment.GetEnvironmentVariable', destination['origins'])
                self.assertNotIn('signature', destination)
                self.assertFalse(result['source_audit_complete'])

    def test_comments_and_code_shaped_strings_do_not_become_inputs(self):
        raw = b'// System.Environment.GetEnvironmentVariable("OWNER")\n' + self.raw
        raw = raw.replace(b'"Core"', b'"System.Environment.GetEnvironmentVariable(OWNER)"')
        result = self.analyze(raw)
        self.assertEqual(result['unclassified'], [])
        self.assertEqual(result['effects'][2]['elements'][0]['value'], 'System.Environment.GetEnvironmentVariable(OWNER)')
        self.assertEqual(result['effects'][2]['origins'], [])

    def test_source_order_and_expanded_or_array_params_are_preserved(self):
        lines = self.raw.splitlines(keepends=True)
        private = next(i for i, line in enumerate(lines) if b'PrivateDependencyModuleNames.AddRange' in line)
        third = next(i for i, line in enumerate(lines) if b'AddEngineThirdPartyPrivateStaticDependencies' in line)
        lines[private], lines[third] = lines[third], lines[private]
        reordered = self.analyze(b''.join(lines))
        self.assertEqual(reordered['effects'][3]['signature'], self.analysis.THIRD_PARTY)
        self.assertEqual(reordered['effects'][4]['signature'], self.analysis.ADD_RANGE)
        for value, form in ((b'Target, "OpenSSL", "Second"', 'expanded'),
                            (b'Target, new[] { "OpenSSL", "Second" }', 'array')):
            with self.subTest(form=form):
                effect = self.analyze(self.raw.replace(b'Target, "OpenSSL"', value))['effects'][-1]
                self.assertEqual(effect['signature'], self.analysis.THIRD_PARTY)
                self.assertEqual(effect['params_form'], form)
                self.assertEqual([v['value'] for v in effect['elements']], ['OpenSSL', 'Second'])

    def test_target_string_and_unknown_setter_do_not_receive_known_bindings(self):
        for raw, callee in ((self.raw.replace(b'Dependencies(Target,', b'Dependencies("Target",'), 'AddEngineThirdPartyPrivateStaticDependencies'),
                            (self.raw.replace(b'PCHUsage =', b'HiddenState ='), 'HiddenState')):
            with self.subTest(callee=callee):
                result = self.analyze(raw)
                self.assertTrue(any(e['callee'] == callee for e in result['unclassified']))
                self.assertTrue(any('signature' not in e for e in result['effects']))

    def test_missing_changed_or_extra_engine_body_rejects_the_summary_profile(self):
        for name in self.engine:
            changed = dict(self.engine)
            changed[name] += b'\n// changed\n'
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, '^lcer.build_rule_api_identity_mismatch$'):
                self.analysis.analyze(self.path, self.raw, changed)
        missing = dict(self.engine)
        missing.pop('ModuleRules.Obsolete.cs')
        extra = dict(self.engine, **{'UndeclaredPartial.cs': b'public partial class ModuleRules {}'})
        for sources in (missing, extra):
            with self.assertRaisesRegex(ValueError, '^lcer.build_rule_api_identity_mismatch$'):
                self.analysis.analyze(self.path, self.raw, sources)


class FixedPipeCleanupTests(unittest.TestCase):
    def pipes(self):
        pairs = [os.pipe() for _ in range(3)]
        def cleanup():
            for pair in pairs:
                for fd in pair:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
        self.addCleanup(cleanup)
        process = OriginalPipeProcess(None)
        process.stdin_fd, process.stdout_fd, process.stderr_fd = [pair[0] for pair in pairs]
        return process, pairs

    def test_success_closes_owned_descriptors_and_repeated_cleanup_is_inert(self):
        process, pairs = self.pipes()
        process.close_pipes()
        self.assertEqual((process.stdin_fd, process.stdout_fd, process.stderr_fd), (None, None, None))
        for reader, writer in pairs:
            with self.assertRaises(OSError):
                os.fstat(reader)
            os.fstat(writer)
        process.close_pipes()

    def test_middle_close_failure_preserves_failed_and_later_descriptor_state(self):
        process, pairs = self.pipes()
        failed, later = process.stdout_fd, process.stderr_fd
        os.close(failed)
        with self.assertRaises(OSError):
            process.close_pipes()
        self.assertIsNone(process.stdin_fd)
        self.assertEqual((process.stdout_fd, process.stderr_fd), (failed, later))
        os.fstat(later)


class ClangSourceInventoryTests(unittest.TestCase):
    """Real compiler cursors for disposable source; no executable is emitted."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier
        self.reader = verifier.ClangSourceInventory()
        self.temporary = tempfile.TemporaryDirectory(prefix='city-clang-source-', dir='/private/tmp')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / 'fixture.cpp'
        self.argv = ['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang',
                     '-x', 'c++', '-std=c++20', '-fsyntax-only']

    def parse(self, source, extra=None):
        self.path.write_text(source)
        paths = [str(self.path)]
        for name, raw in (extra or {}).items():
            path = self.root / name
            path.write_text(raw)
            paths.append(str(path))
        return self.reader.parse(self.path, paths, self.argv)

    def test_actual_calls_fields_operators_and_parameter_positions_are_derived(self):
        result = self.parse('extern "C" int platform_value();\n'
                            'int relay(int value) { return value; }\n'
                            'struct Box { int owner; int read() const { return owner; } };\n'
                            'int choose(Box &box) { box.owner = relay(platform_value()); return box.read(); }\n')
        self.assertEqual(result['parse_returncode'], 0)
        self.assertEqual(result['diagnostics'], [])
        self.assertEqual(result['visitor_errors'], [])
        self.assertTrue(result['source_snapshot_unchanged'] and result['library_snapshot_unchanged'])
        self.assertFalse(result['source_audit_complete'])
        calls = [row for row in result['references'] if row['kind'] == 'CallExpr']
        self.assertEqual({row['target'] for row in calls}, {'relay', 'platform_value', 'Box::read'})
        self.assertTrue(all(row['target_usr'] for row in calls))
        field = next(node for node in result['nodes'] if node['kind'] == 'FieldDecl')
        self.assertEqual(field['usr'], 'c:@S@Box@FI@owner')
        assignment = next(node for node in result['nodes'] if node['binary_operator'] == '=')
        self.assertEqual(assignment['location']['path'], str(self.path))
        relay = next(row for row in calls if row['target'] == 'relay')
        self.assertEqual(len(result['nodes'][relay['node']]['arguments']), 1)
        self.assertEqual(result['nodes'][relay['node']]['arguments'][0]['index'], 0)
        argument = result['nodes'][relay['node']]['arguments'][0]
        self.assertEqual(len(argument['cursor_nodes']), 1)
        self.assertEqual(result['nodes'][argument['cursor_nodes'][0]]['name'], 'platform_value')
        method = next(node for node in result['nodes'] if node['kind'] == 'CXXMethod')
        self.assertEqual(method['method_properties'], {'static': False, 'const': True, 'virtual': False})

    def test_overloads_have_distinct_compiler_identities(self):
        result = self.parse('int choose(int value) { return value; }\n'
                            'double choose(double value) { return value; }\n'
                            'int invoke() { return choose(1) + int(choose(2.0)); }\n')
        definitions = [row for row in result['declarations'] if row['name'] == 'choose' and row['definition']]
        self.assertEqual(len(definitions), 2)
        self.assertEqual(len({row['usr'] for row in definitions}), 2)
        calls = [row for row in result['references'] if row['kind'] == 'CallExpr' and row['target'] == 'choose']
        self.assertEqual({row['target_usr'] for row in calls}, {row['usr'] for row in definitions})

    def test_external_call_bindings_keep_overloads_receivers_and_constructor_result(self):
        graph = self.cpp_graph('struct Box { Box(int); int read() const; static int read(int); '
                               'Box &operator=(int); virtual int dynamic() const; };\n'
                               'int entry(int input) { Box box(input); box=input; '
                               'return box.read() + Box::read(input) + box.dynamic(); }\n')
        calls = [c for c in graph['calls'] if c['target'].startswith('Box::')]
        self.assertEqual(len(calls), 5)
        self.assertTrue(all(c['binding']['complete'] for c in calls))
        layouts = {c['binding']['layout']: c for c in calls}
        constructor = layouts['constructor_result']
        self.assertEqual(constructor['binding']['receiver'], constructor['node'])
        self.assertEqual(len(constructor['binding']['arguments']), 1)
        static = layouts['static_method']['binding']
        self.assertIsNone(static['receiver'])
        self.assertEqual(static['arguments'][0]['parameter']['type'], 'int')
        assignment = layouts['operator_receiver_argument']['binding']
        self.assertEqual(len(assignment['arguments']), 1)
        self.assertEqual({graph['nodes'][n]['label'] for n in assignment['receiver_storage']}, {'box'})
        dynamic = next(c for c in calls if c['target'] == 'Box::dynamic')
        self.assertIn({'node': dynamic['node'], 'reason': 'dynamic_call_unresolved'}, graph['unclassified'])
        self.assertEqual(len({c['target_usr'] for c in calls if c['target'] == 'Box::read'}), 2)

    def test_external_void_reference_writes_retain_input_to_caller_storage(self):
        graph = self.cpp_graph('extern int platform_value(); void write(int &, int);\n'
                               'int entry() { int value=0; write(value,platform_value()); return value; }\n')
        self.assertTrue(self.graph_reachable(graph, self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                                            self.graph_nodes(graph, 'return_slot', 'entry')))
        call = next(c for c in graph['calls'] if c['target'] == 'write')
        self.assertEqual(call['binding']['arguments'][0]['parameter']['type_kind'], 'LValueReference')
        self.assertIn({'node': call['node'], 'reason': 'external_call_effect_unresolved'}, graph['unclassified'])

    def test_missing_external_parameter_identity_keeps_binding_unresolved(self):
        inventory = self.parse('void publish(int); void entry() { publish(1); }\n')
        reference = next(r for r in inventory['references'] if r['kind'] == 'CallExpr')
        del reference['target_parameters']
        graph = self.verifier.CppInputFlowGraph([inventory], {str(self.path): self.path.read_bytes()}).build()
        self.assertFalse(graph['calls'][0]['binding']['complete'])
        self.assertIn({'node': graph['calls'][0]['node'], 'reason': 'call_parameter_binding_unresolved'}, graph['unclassified'])

    def test_api_source_snapshot_is_separate_from_traversed_source_and_detects_change(self):
        self.path.write_text('int entry() { return 1; }\n')
        api = self.root / 'api.h'
        api.write_text('int external(int);\n')
        initial = api.read_bytes()
        result = self.reader.parse(self.path, [str(self.path)], self.argv, [str(api)])
        self.assertEqual(result['api_source_hashes'], {str(api): self.verifier.digest(initial)})
        self.assertTrue(result['api_source_snapshot_unchanged'])
        self.assertNotIn(str(api), result['source_hashes'])
        original = self.reader.api['disposeIndex']
        def change_after_parse(index):
            original(index)
            api.write_bytes(initial + b'// changed\n')
        self.reader.api['disposeIndex'] = change_after_parse
        changed = self.reader.parse(self.path, [str(self.path)], self.argv, [str(api)])
        self.assertFalse(changed['api_source_snapshot_unchanged'])

    def test_same_fstring_usr_and_type_in_local_source_cannot_claim_engine_effect(self):
        api = self.verifier.CppStringEffects
        engine = {api.ROOT + name: Path(api.ROOT + name).read_bytes() for name in api.SOURCE_HASHES}
        self.path.write_text('using int32=int; struct FString { int32 Len() const; };\n'
                             'int32 entry(const FString &value) { return value.Len(); }\n')
        inventory = self.reader.parse(self.path, [str(self.path)], self.argv, list(engine))
        call = next(r for r in inventory['references'] if r['kind'] == 'CallExpr')
        self.assertEqual(call['target_usr'], 'c:@S@FString@F@Len#1')
        self.assertEqual(call['target_type'], 'int32 () const')
        graph = self.verifier.CppInputFlowGraph([inventory], {str(self.path): self.path.read_bytes()}, engine).build()
        self.assertTrue(graph['calls'][0]['binding']['complete'])
        self.assertNotIn('api_effect', graph['calls'][0])
        self.assertIn({'node': graph['calls'][0]['node'], 'reason': 'external_call_effect_unresolved'}, graph['unclassified'])

    def test_string_api_source_identity_requires_all_bodies_and_unchanged_inventory(self):
        api = self.verifier.CppStringEffects
        sources = {api.ROOT + name: Path(api.ROOT + name).read_bytes() for name in api.SOURCE_HASHES}
        hashes = {name: self.verifier.digest(raw) for name, raw in sources.items()}
        record = {'api_source_hashes': hashes, 'api_source_snapshot_unchanged': True}
        self.assertEqual(api([record], sources).source_hashes, hashes)
        for name in sources:
            with self.subTest(source=name):
                changed = dict(sources, **{name: sources[name] + b'\n'})
                # Rehashing the supplied inventory cannot replace the pinned
                # implementation with a different body.
                rehashed = dict(record, api_source_hashes={p: self.verifier.digest(raw) for p, raw in changed.items()})
                with self.assertRaisesRegex(ValueError, 'lcer.string_api_identity_mismatch'):
                    api([rehashed], changed)
        variants = [(dict(record, api_source_snapshot_unchanged=False), sources),
                    (dict(record, api_source_hashes={}), sources),
                    (record, dict(sources, extra=b'')), (record, {})]
        for inventory, raw in variants:
            with self.assertRaisesRegex(ValueError, 'lcer.string_api_identity_mismatch'):
                api([inventory], raw)
        with self.assertRaisesRegex(ValueError, 'lcer.string_api_identity_mismatch'):
            api([], sources)

    def test_json_api_pins_reject_rehashed_bodies_and_support_separately_bound_families(self):
        api = self.verifier.CppJsonMemoryEffects
        sources = {api.ROOT + name: Path(api.ROOT + name).read_bytes() for name in api.SOURCE_HASHES}
        strings = self.verifier.CppStringEffects
        string_sources = {strings.ROOT + name: Path(strings.ROOT + name).read_bytes() for name in strings.SOURCE_HASHES}
        combined = dict(sources, **string_sources)
        hashes = {name: self.verifier.digest(raw) for name, raw in combined.items()}
        inventory = {'api_source_hashes': hashes, 'api_source_snapshot_unchanged': True}
        self.assertEqual(set(api([inventory], sources).source_hashes), set(sources))
        self.assertEqual(set(strings([inventory], string_sources).source_hashes), set(string_sources))
        for path in sources:
            with self.subTest(path=path):
                changed = dict(sources, **{path: sources[path] + b'\n'})
                rehashed = dict(inventory, api_source_hashes=dict(hashes, **{path: self.verifier.digest(changed[path])}))
                with self.assertRaisesRegex(ValueError, 'lcer.json_api_identity_mismatch'):
                    api([rehashed], changed)
        for raw in ({}, dict(sources, extra=b'')):
            with self.assertRaisesRegex(ValueError, 'lcer.json_api_identity_mismatch'):
                api([inventory], raw)
        for changed in (dict(inventory, api_source_snapshot_unchanged=False), dict(inventory, api_source_hashes={})):
            with self.assertRaisesRegex(ValueError, 'lcer.json_api_identity_mismatch'):
                api([changed], sources)

    def test_local_shared_pointer_with_engine_usr_cannot_claim_json_handle_effect(self):
        api = self.verifier.CppJsonMemoryEffects
        sources = {api.ROOT + name: Path(api.ROOT + name).read_bytes() for name in api.SOURCE_HASHES}
        self.path.write_text('enum class ESPMode { NotThreadSafe, ThreadSafe }; class FJsonObject {};\n'
                             'template<class T, ESPMode M> struct TSharedPtr { bool IsValid() const; };\n'
                             'bool entry(const TSharedPtr<FJsonObject, ESPMode::ThreadSafe>& value) { return value.IsValid(); }\n')
        inventory = self.reader.parse(self.path, [str(self.path)], self.argv, list(sources))
        reference = next(r for r in inventory['references'] if r['kind'] == 'CallExpr')
        self.assertEqual(reference['target_usr'], 'c:@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1@F@IsValid#1')
        self.assertEqual(reference['target_type'], 'bool () const')
        graph = self.verifier.CppInputFlowGraph([inventory], {str(self.path): self.path.read_bytes()},
                                               json_api_source_bytes=sources).build()
        self.assertTrue(graph['calls'][0]['binding']['complete'])
        self.assertNotIn('api_effect', graph['calls'][0])
        self.assertIn({'node': graph['calls'][0]['node'], 'reason': 'external_call_effect_unresolved'}, graph['unclassified'])

    def test_local_header_definitions_are_bound_and_enumerated(self):
        result = self.parse('#include "helper.h"\nint entry() { return helper(1); }\n',
                            {'helper.h': 'inline int helper(int value) { return value; }\n'})
        helper = next(row for row in result['declarations'] if row['name'] == 'helper')
        self.assertEqual(helper['expansion']['path'], str(self.root / 'helper.h'))
        self.assertEqual(set(result['source_hashes']), {str(self.path), str(self.root / 'helper.h')})
        self.assertEqual(result['diagnostics'], [])

    def test_malformed_source_retains_diagnostics_without_an_audit_pass(self):
        result = self.parse('int broken( { return unknown_name; }\n')
        self.assertTrue(any(row['severity'] >= 3 for row in result['diagnostics']))
        self.assertFalse(result['source_audit_complete'])

    def test_response_and_compiler_plugin_options_are_rejected_with_exact_edge(self):
        self.path.write_text('int value() { return 1; }\n')
        for option in ('@unverified.rsp', '-load', '-fplugin=unverified.dylib', '-fpass-plugin=unverified.dylib'):
            with self.subTest(option=option):
                with self.assertRaises(self.verifier.SourceInputForbidden) as failure:
                    self.reader.parse(self.path, [str(self.path)], [*self.argv, option])
                self.assertEqual(failure.exception.edge, {'path': str(self.path), 'function': '<compiler>',
                                  'input': 'platform', 'callee': option, 'line': 0})

    def cpp_graph(self, source, extra=None):
        inventory = self.parse(source, extra)
        sources = {str(self.path): self.path.read_bytes()}
        sources.update({str(self.root / name): (self.root / name).read_bytes() for name in (extra or {})})
        return self.verifier.CppInputFlowGraph([inventory], sources).build()

    def graph_nodes(self, graph, kind=None, label=None, function=None):
        return {n['id'] for n in graph['nodes'] if (kind is None or n['kind'] == kind)
                and (label is None or n['label'] == label) and (function is None or n['function'] == function)}

    def graph_reachable(self, graph, starts, ends):
        outgoing = {}
        for edge in graph['edges']:
            outgoing.setdefault(edge['source'], set()).add(edge['target'])
        pending, seen = list(starts), set()
        while pending:
            node = pending.pop()
            if node in ends:
                return True
            if node not in seen:
                seen.add(node)
                pending.extend(outgoing.get(node, ()))
        return False

    def test_cpp_graph_traces_external_input_through_actual_local_helper(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'int relay(int value) { return value; }\n'
                               'int owner() { return relay(platform_value()); }\n')
        source = self.graph_nodes(graph, 'CallExpr', 'platform_value()')
        target = self.graph_nodes(graph, 'return_slot', 'owner')
        self.assertTrue(source and target and self.graph_reachable(graph, source, target))
        call = next(c for c in graph['calls'] if c['node'] in source)
        self.assertFalse(call['local_definition'])
        self.assertIn({'node': call['node'], 'reason': 'external_call_effect_unresolved'}, graph['unclassified'])
        self.assertFalse(graph['source_audit_complete'])

    def test_cpp_graph_out_reference_write_reaches_caller_storage(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'void assign(int &out) { out = platform_value(); }\n'
                               'int owner() { int value = 0; assign(value); return value; }\n')
        self.assertTrue(self.graph_reachable(graph,
                        self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                        self.graph_nodes(graph, 'return_slot', 'owner')))
        self.assertTrue(any(e['kind'] == 'may_reference_write' for e in graph['edges']))
        self.assertTrue(any(e['reason'] == 'reference_call_effect_unresolved' for e in graph['unclassified']))

    def test_cpp_separate_calls_do_not_mix_argument_derived_returns(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'int relay(int value) { return value; }\n'
                               'int entry() { int unused = relay(platform_value()); return relay(1); }\n')
        source = self.graph_nodes(graph, 'CallExpr', 'platform_value()')
        self.assertTrue(self.graph_reachable(graph, source, self.graph_nodes(graph, 'storage', 'unused')))
        self.assertFalse(self.graph_reachable(graph, source, self.graph_nodes(graph, 'return_slot', 'entry')))
        calls = [c for c in graph['calls'] if c['target'] == 'relay']
        self.assertEqual(len(calls), 2)
        self.assertTrue(set(p['node'] for p in calls[0]['ports']).isdisjoint(p['node'] for p in calls[1]['ports']))

    def test_cpp_unused_argument_does_not_become_a_return_value_or_activation(self):
        graph = self.cpp_graph('extern int platform_value();\nint owner;\n'
                               'int constant(int unused) { owner = 1; return 7; }\n'
                               'int entry() { return constant(platform_value()); }\n')
        source = self.graph_nodes(graph, 'CallExpr', 'platform_value()')
        self.assertFalse(self.graph_reachable(graph, source, self.graph_nodes(graph, 'return_slot', 'entry')))
        self.assertFalse(self.graph_reachable(graph, source, self.graph_nodes(graph, 'storage', 'owner')))

    def test_cpp_reference_writes_are_bound_to_the_correct_call(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'void assign(int &out, int input) { out = input; }\n'
                               'int entry() { int first = 0, second = 0; assign(first, platform_value()); '
                               'assign(second, 1); return second; }\n')
        source = self.graph_nodes(graph, 'CallExpr', 'platform_value()')
        self.assertTrue(self.graph_reachable(graph, source, self.graph_nodes(graph, 'storage', 'first')))
        self.assertFalse(self.graph_reachable(graph, source, self.graph_nodes(graph, 'storage', 'second')))
        self.assertFalse(self.graph_reachable(graph, source, self.graph_nodes(graph, 'return_slot', 'entry')))

    def test_cpp_global_writes_remain_shared_between_calls(self):
        graph = self.cpp_graph('extern int platform_value();\nint owner;\n'
                               'void assign(int input) { owner = input; }\nint read() { return owner; }\n'
                               'int entry() { assign(platform_value()); return read(); }\n')
        self.assertTrue(self.graph_reachable(graph, self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                        self.graph_nodes(graph, 'return_slot', 'entry')))

    def test_cpp_static_and_thread_local_cells_keep_persistent_storage(self):
        for qualifier in ('static', 'thread_local'):
            with self.subTest(qualifier=qualifier):
                graph = self.cpp_graph('extern int platform_value();\n'
                                       'int remember(int input, bool write) { ' + qualifier + ' int owner = 0; '
                                       'if (write) owner = input; return owner; }\n'
                                       'int entry() { remember(platform_value(), true); return remember(0, false); }\n')
                self.assertTrue(self.graph_reachable(graph, self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                                self.graph_nodes(graph, 'return_slot', 'entry')))

    def test_cpp_nested_calls_preserve_context_and_intrinsic_input(self):
        for body, expected in (('return inner(value);', False), ('return inner(platform_value());', True)):
            with self.subTest(body=body):
                graph = self.cpp_graph('extern int platform_value();\nint inner(int value) { return value; }\n'
                                       'int outer(int value) { ' + body + ' }\n'
                                       'int entry() { outer(platform_value()); return outer(1); }\n')
                self.assertEqual(self.graph_reachable(graph, self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                                 self.graph_nodes(graph, 'return_slot', 'entry')), expected)
                self.assertFalse(self.graph_reachable(graph,
                                 self.graph_nodes(graph, 'CallExpr', 'platform_value()', 'entry'),
                                 self.graph_nodes(graph, 'return_slot', 'entry')))

    def test_cpp_recursive_calls_reach_a_fixed_point_without_cross_call_mixing(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'int recurse(int value, int count) { if (count) return recurse(value, count - 1); return value; }\n'
                               'int entry() { int unused = recurse(platform_value(), 2); return recurse(1, 2); }\n')
        source = self.graph_nodes(graph, 'CallExpr', 'platform_value()')
        self.assertTrue(self.graph_reachable(graph, source, self.graph_nodes(graph, 'storage', 'unused')))
        self.assertFalse(self.graph_reachable(graph, source, self.graph_nodes(graph, 'return_slot', 'entry')))
        self.assertTrue(all(s['fixed_point_iterations'] < 256 for s in graph['call_summaries']))

    def test_cpp_helper_effect_inputs_remain_in_the_body_summary(self):
        graph = self.cpp_graph('extern void publish(int);\nvoid relay(int input) { publish(input); }\n'
                               'void entry(int value) { relay(value); }\n')
        function = next(f for f in graph['functions'] if f['name'] == 'relay')
        summary = next(s for s in graph['call_summaries'] if s['usr'] == function['usr'])
        effect = next(c for c in graph['calls'] if c['target'] == 'publish')
        inputs = next(e['inputs'] for e in summary['effects'] if e['node'] == effect['node'])
        self.assertIn(function['parameters'][0], inputs)
        self.assertTrue(any(u['node'] == effect['node'] and u['reason'] == 'external_call_effect_unresolved'
                            for u in graph['unclassified']))
        caller = next(f for f in graph['functions'] if f['name'] == 'entry')
        caller_summary = next(s for s in graph['call_summaries'] if s['usr'] == caller['usr'])
        call = next(c for c in graph['calls'] if c['target'] == 'relay')
        caller_effect = next(e for e in caller_summary['effects'] if e['node'] == call['node'])
        self.assertIn(caller['parameters'][0], caller_effect['inputs'])
        binding = next(b for b in caller_effect['bindings'] if b['template'] == function['parameters'][0])
        self.assertIn(caller['parameters'][0], binding['inputs'])
        self.assertFalse(graph['source_audit_complete'])

    def test_cpp_mutual_recursion_preserves_reference_effects_per_call(self):
        graph = self.cpp_graph('extern int platform_value();\nvoid odd(int&, int, int);\n'
                               'void even(int &out, int value, int depth) { if (depth) odd(out, value, depth - 1); else out = value; }\n'
                               'void odd(int &out, int value, int depth) { even(out, value, depth); }\n'
                               'int entry() { int first = 0, second = 0; odd(first, platform_value(), 2); '
                               'odd(second, 1, 2); return second; }\n')
        source = self.graph_nodes(graph, 'CallExpr', 'platform_value()')
        self.assertTrue(self.graph_reachable(graph, source, self.graph_nodes(graph, 'storage', 'first')))
        self.assertFalse(self.graph_reachable(graph, source, self.graph_nodes(graph, 'return_slot', 'entry')))

    def test_cpp_summary_budget_failure_returns_no_partial_graph(self):
        from unittest import mock
        with mock.patch.object(self.verifier.CppInputFlowGraph, 'MAX_SUMMARY_ITERATIONS', 1):
            with self.assertRaisesRegex(ValueError, '^lcer.call_summary_budget_exceeded$'):
                self.cpp_graph('int relay(int value) { return value; }\nint entry() { return relay(1); }\n')
        with mock.patch.object(self.verifier.CppInputFlowGraph, 'MAX_SUMMARY_EDGES', 1):
            with self.assertRaisesRegex(ValueError, '^lcer.call_summary_budget_exceeded$'):
                self.cpp_graph('int relay(int value) { return value; }\nint entry() { return relay(1); }\n')

    def test_cpp_missing_storage_duration_keeps_a_shared_unresolved_path(self):
        inventory = self.parse('extern int platform_value();\n'
                               'int remember(int input, bool write) { static int owner = 0; if (write) owner = input; return owner; }\n'
                               'int entry() { remember(platform_value(), true); return remember(0, false); }\n')
        for node in inventory['nodes']:
            if node['kind'] == 'VarDecl' and node['name'] == 'owner':
                self.assertTrue(node.pop('global_storage'))
        graph = self.verifier.CppInputFlowGraph([inventory], {str(self.path): self.path.read_bytes()}).build()
        self.assertTrue(any(u['reason'] == 'storage_duration_unresolved' for u in graph['unclassified']))
        self.assertTrue(self.graph_reachable(graph, self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                        self.graph_nodes(graph, 'return_slot', 'entry')))

    def test_cpp_graph_field_reads_keep_storage_and_object_uncertainty(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'struct Box { int owner; int read() const { return owner; } };\n'
                               'int choose(Box &box) { box.owner = platform_value(); return box.read(); }\n')
        self.assertTrue(self.graph_reachable(graph,
                        self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                        self.graph_nodes(graph, 'return_slot', 'choose')))
        fields = [n for n in graph['nodes'] if n['kind'] == 'storage' and n['usr'] == 'c:@S@Box@FI@owner']
        self.assertEqual(len(fields), 1)
        self.assertTrue(any(e['reason'] == 'object_sensitive_storage_unresolved' for e in graph['unclassified']))

    def test_cpp_graph_retains_conditional_and_short_circuit_helper_effects(self):
        graph = self.cpp_graph('extern bool platform_flag();\n'
                               'int owner; bool set_owner() { owner = 1; return true; }\n'
                               'void choose() { platform_flag() && set_owner(); }\n')
        self.assertTrue(self.graph_reachable(graph,
                        self.graph_nodes(graph, 'CallExpr', 'platform_flag()'),
                        self.graph_nodes(graph, 'storage', 'owner')))
        self.assertTrue(any(e['kind'] == 'short_circuit_control' for e in graph['edges']))
        self.assertTrue(any(e['reason'] == 'control_flow_dominance_unresolved' for e in graph['unclassified']))

    def test_cpp_graph_distinguishes_overload_returns(self):
        graph = self.cpp_graph('int choose(int value) { return value; }\n'
                               'double choose(double value) { return value; }\n'
                               'int invoke() { return choose(1); }\n')
        choices = [f for f in graph['functions'] if f['name'] == 'choose']
        self.assertEqual(len(choices), 2)
        call = next(c for c in graph['calls'] if c['target'] == 'choose')
        selected = next(f for f in choices if f['usr'] == call['target_usr'])
        other = next(f for f in choices if f['usr'] != call['target_usr'])
        ports = {p['template']: p['node'] for p in call['ports']}
        self.assertEqual(graph['nodes'][ports[selected['return']]]['usr'], selected['usr'])
        self.assertTrue(self.graph_reachable(graph, {ports[selected['parameters'][0]]}, {call['node']}))
        self.assertFalse(self.graph_reachable(graph, {selected['return']}, {call['node']}))
        self.assertFalse(self.graph_reachable(graph, {other['return']}, {call['node']}))

    def test_cpp_graph_header_helper_uses_actual_definition(self):
        graph = self.cpp_graph('#include "helper.h"\nint owner() { return helper(); }\n',
                               {'helper.h': 'extern int platform_value();\ninline int helper() { return platform_value(); }\n'})
        call = next(c for c in graph['calls'] if c['target'] == 'helper')
        self.assertTrue(call['local_definition'])
        self.assertTrue(self.graph_reachable(graph,
                        self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                        self.graph_nodes(graph, 'return_slot', 'owner')))

    def test_cpp_graph_operator_receiver_is_separate_from_declared_argument(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'struct Box { int owner; int operator+(int value) const { return owner + value; } };\n'
                               'int choose(Box &box) { return box + platform_value(); }\n')
        call = next(c for c in graph['calls'] if c['target'] == 'Box::operator+')
        self.assertTrue(call['local_definition'])
        self.assertTrue(self.graph_reachable(graph,
                        self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                        self.graph_nodes(graph, 'return_slot', 'choose')))
        self.assertNotIn({'node': call['node'], 'reason': 'call_parameter_binding_unresolved'}, graph['unclassified'])
        self.assertTrue(any(e['kind'] == 'receiver_argument' for e in graph['edges']))

    def test_cpp_argument_identity_does_not_confuse_nested_conversions(self):
        inventory = self.parse('struct Value { Value(const char*); Value(const Value&); };\n'
                               'int read(Value value) { return 1; }\n'
                               'int entry() { return read(Value("name")); }\n')
        ref = next(row for row in inventory['references'] if row['kind'] == 'CallExpr' and row['target'] == 'read')
        argument = inventory['nodes'][ref['node']]['arguments'][0]
        self.assertEqual(len(argument['cursor_nodes']), 1)
        selected = inventory['nodes'][argument['cursor_nodes'][0]]
        self.assertEqual(selected['kind'], argument['kind'])
        self.assertEqual(selected['start'], argument['start'])
        self.assertEqual(selected['end'], argument['end'])
        graph = self.verifier.CppInputFlowGraph([inventory], {str(self.path): self.path.read_bytes()}).build()
        call = next(row for row in graph['calls'] if row['target'] == 'read')
        self.assertNotIn({'node': call['node'], 'reason': 'call_argument_cursor_unresolved'}, graph['unclassified'])

    def test_cpp_argument_reference_in_initializer_binds_actual_declaration(self):
        inventory = self.parse('int next(int &index) { return index++; }\n'
                               'int entry() { int index = 0; const int result = next(index); return result; }\n')
        ref = next(row for row in inventory['references'] if row['kind'] == 'CallExpr' and row['target'] == 'next')
        argument = inventory['nodes'][ref['node']]['arguments'][0]
        self.assertEqual(len(argument['cursor_nodes']), 1)
        node = inventory['nodes'][argument['cursor_nodes'][0]]
        self.assertEqual(node['parent'], ref['node'])
        self.assertEqual(node['name'], 'index')
        self.assertIn(argument['identity_basis'], ('cursor_equality', 'direct_reference_declaration'))

    def test_cpp_unnamed_parameter_slot_does_not_invent_a_compiler_usr(self):
        graph = self.cpp_graph('int take(int) { return 1; }\nint entry() { return take(2); }\n')
        function = next(row for row in graph['functions'] if row['name'] == 'take')
        parameter = graph['nodes'][function['parameters'][0]]
        self.assertEqual(parameter['usr'], '')
        self.assertEqual(parameter['storage_identity'], 'parameter-slot:' + function['usr'] + ':0')

    def test_cpp_macro_argument_keeps_its_compiler_owned_subtree(self):
        inventory = self.parse('constexpr bool equal(const char* a, const char* b) { return *a == *b; }\n'
                               'template<bool> struct Check {};\n'
                               'struct Choice { static int condition(Check<true>) { return 1; } '
                               'static int condition(Check<false>) { return 0; } };\n'
                               '#define REGISTER(name) static int registered = Choice::condition(Check<equal(#name, #name)>());\n'
                               'REGISTER(Module)\n')
        call = next(n for n in inventory['nodes'] if n['kind'] == 'CallExpr' and n['name'] == 'condition')
        argument = call['arguments'][0]
        self.assertEqual(argument['identity_basis'], 'compiler_argument_subtree')
        self.assertEqual(len(argument['cursor_nodes']), 1)
        root = inventory['nodes'][argument['cursor_nodes'][0]]
        self.assertEqual(root['parent'], call['id'])
        self.assertEqual(root['argument_owner'], {'call': call['id'], 'index': 0})
        self.assertEqual(root['kind'], 'CallExpr')
        self.assertEqual(root['name'], 'Check')
        self.assertEqual(root['usr'], '')
        self.assertEqual(inventory['diagnostics'], [])
        self.assertEqual(inventory['visitor_errors'], [])
        graph = self.verifier.CppInputFlowGraph([inventory], {str(self.path): self.path.read_bytes()}).build()
        invocation = next(c for c in graph['calls'] if c['target'] == 'Choice::condition')
        self.assertNotIn({'node': invocation['node'], 'reason': 'call_argument_cursor_unresolved'}, graph['unclassified'])
        selected = next(f for f in graph['functions'] if f['usr'] == invocation['target_usr'])
        ports = {p['template']: p['node'] for p in invocation['ports']}
        self.assertTrue(self.graph_reachable(graph, self.graph_nodes(graph, 'StringLiteral'),
                        {ports[p] for p in selected['parameters']}))
        self.assertFalse(graph['source_audit_complete'])

    def test_cpp_lambda_body_has_its_actual_call_operator_identity(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'int entry() { auto choose = [](int value) { return value; }; return choose(platform_value()); }\n')
        lambdas = self.graph_nodes(graph, 'LambdaExpr')
        self.assertEqual(len(lambdas), 1)
        self.assertFalse(any(row['node'] in lambdas and row['reason'] == 'anonymous_callable_identity_unresolved'
                             for row in graph['unclassified']))
        call = next(row for row in graph['calls'] if row['target'].endswith('::operator()'))
        self.assertTrue(call['local_definition'])
        self.assertIn(call['target_usr'], {row['usr'] for row in graph['functions']})
        self.assertTrue(self.graph_reachable(graph,
                        self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                        self.graph_nodes(graph, 'return_slot', 'entry')))
        self.assertFalse(graph['source_audit_complete'])

    def test_cpp_missing_lambda_identity_remains_unresolved(self):
        inventory = self.parse('int entry() { auto choose = [](int value) { return value; }; return choose(1); }\n')
        for node in inventory['nodes']:
            if node['kind'] == 'LambdaExpr':
                node.pop('lambda_operator_node')
        graph = self.verifier.CppInputFlowGraph([inventory], {str(self.path): self.path.read_bytes()}).build()
        self.assertTrue(any(row['reason'] == 'anonymous_callable_identity_unresolved' for row in graph['unclassified']))

    def test_cpp_lambda_capture_initializer_and_operator_body_are_each_visited_once(self):
        inventory = self.parse('extern int platform_value();\nint relay(int value) { return value; }\n'
                               'int entry() { auto choose = [owner = platform_value()](int value) { return relay(value) + owner; }; return choose(1); }\n')
        calls = [row for row in inventory['references'] if row['kind'] == 'CallExpr']
        self.assertEqual(sum(row['target'] == 'platform_value' for row in calls), 1)
        self.assertEqual(sum(row['target'] == 'relay' for row in calls), 1)
        self.assertEqual(next(row['function'] for row in calls if row['target'] == 'platform_value'), 'entry')
        operators = [row for row in inventory['declarations'] if row['kind'] == 'CXXMethod' and row['name'].endswith('::operator()')]
        self.assertEqual(len(operators), 1)
        graph = self.verifier.CppInputFlowGraph([inventory], {str(self.path): self.path.read_bytes()}).build()
        self.assertTrue(any(row['reason'] == 'lambda_capture_semantics_unresolved' for row in graph['unclassified']))
        self.assertTrue(self.graph_reachable(graph,
                        self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                        self.graph_nodes(graph, 'return_slot', 'entry')))

    def test_cpp_mixed_captures_do_not_replay_outer_initializers_or_duplicate_calls(self):
        inventory = self.parse('extern int platform_value();\n'
                               'int entry() { int before = platform_value(); auto choose = '
                               '[a = platform_value() + platform_value(), before, b = platform_value(), c = 3]() '
                               '{ return a + before + b + c; }; return choose(); }\n')
        calls = [row for row in inventory['references'] if row['kind'] == 'CallExpr' and row['target'] == 'platform_value']
        self.assertEqual(len(calls), 4)
        self.assertEqual({row['function'] for row in calls}, {'entry'})
        expression = next(n for n in inventory['nodes'] if n['kind'] == 'LambdaExpr')
        declarations = [inventory['nodes'][number] for number in expression['lambda_initializer_nodes']]
        self.assertEqual([node['name'] for node in declarations], ['a', 'b', 'c'])
        self.assertEqual(inventory['diagnostics'], [])
        self.assertEqual(inventory['visitor_errors'], [])

    def test_cpp_capture_fields_keep_real_empty_usrs_and_compiler_layout(self):
        inventory = self.parse('int entry() { int copied = 1; int aliased = 2; auto choose = [copied, &aliased]() { return copied + aliased; }; return choose(); }\n')
        closure = next(n['lambda_closure'] for n in inventory['nodes'] if n['kind'] == 'LambdaExpr')
        self.assertTrue(closure['usr'])
        self.assertEqual(len(closure['fields']), 2)
        self.assertEqual([field['usr'] for field in closure['fields']], ['', ''])
        self.assertEqual([field['ordinal'] for field in closure['fields']], [0, 1])
        self.assertEqual([field['type_kind'] for field in closure['fields']], ['Int', 'LValueReference'])
        self.assertTrue(all(field['offset_bits'] >= 0 for field in closure['fields']))

    def test_cpp_generic_lambda_requires_its_own_operator_resolution(self):
        graph = self.cpp_graph('int entry() { auto choose = [](auto value) { return value; }; return choose(1); }\n')
        self.assertTrue(any(row['reason'] == 'anonymous_callable_identity_unresolved' for row in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])

    def test_cpp_reference_capture_writes_reach_the_original_storage(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'int entry() { int owner = 0; auto choose = [&owner]() { owner = platform_value(); }; choose(); return owner; }\n')
        self.assertTrue(self.graph_reachable(graph,
                        self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                        self.graph_nodes(graph, 'storage', 'owner')))
        capture = next(n for n in graph['nodes'] if n['kind'] == 'capture_storage')
        self.assertEqual(capture['capture_mode'], 'reference')
        self.assertEqual(capture['usr'], '')
        self.assertTrue(capture['storage_identity'].startswith('lambda-capture:'))
        self.assertTrue(any(u['reason'] == 'lambda_instance_storage_unresolved' for u in graph['unclassified']))

    def test_cpp_mutable_copy_capture_does_not_write_back_to_original(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'int entry() { int owner = 0; auto choose = [owner]() mutable { owner = platform_value(); }; choose(); return owner; }\n')
        source = self.graph_nodes(graph, 'CallExpr', 'platform_value()')
        self.assertTrue(self.graph_reachable(graph, source, self.graph_nodes(graph, 'capture_storage', 'owner')))
        self.assertFalse(self.graph_reachable(graph, source, self.graph_nodes(graph, 'storage', 'owner')))
        self.assertFalse(self.graph_reachable(graph, source, self.graph_nodes(graph, 'return_slot', 'entry')))
        self.assertEqual(next(n['capture_mode'] for n in graph['nodes'] if n['kind'] == 'capture_storage'), 'copy')

    def test_cpp_capture_of_reference_by_value_still_copies_its_scalar(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'int entry() { int owner = 0; int &alias = owner; auto choose = [alias]() mutable '
                               '{ alias = platform_value(); }; choose(); return owner; }\n')
        self.assertFalse(self.graph_reachable(graph,
                         self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                         self.graph_nodes(graph, 'storage', 'owner')))
        self.assertEqual(next(n['capture_mode'] for n in graph['nodes'] if n['kind'] == 'capture_storage'), 'copy')

    def test_cpp_default_capture_and_nontrivial_copy_remain_unresolved(self):
        for source in ('int entry() { int owner = 0; auto choose = [=]() { return owner; }; return choose(); }\n',
                       'struct Box { Box(const Box&); int owner; }; int entry(Box &box) { '
                       'auto choose = [box]() { return box.owner; }; return choose(); }\n'):
            with self.subTest(source=source):
                graph = self.cpp_graph(source)
                self.assertTrue(any(u['reason'] == 'lambda_capture_semantics_unresolved' for u in graph['unclassified']))
                self.assertFalse(graph['source_audit_complete'])

    def test_cpp_external_variable_read_reaches_local_helper_return(self):
        graph = self.cpp_graph('extern int platform_owner;\n'
                               'int relay(int value) { return value; }\n'
                               'int choose() { return relay(platform_owner); }\n')
        external = self.graph_nodes(graph, 'external_storage', 'platform_owner')
        self.assertEqual(len(external), 1)
        self.assertTrue(self.graph_reachable(graph, external, self.graph_nodes(graph, 'return_slot', 'choose')))
        self.assertTrue(any(row['reason'] == 'external_storage_origin_unresolved' for row in graph['unclassified']))

    def test_cpp_header_external_variable_write_keeps_exact_target(self):
        graph = self.cpp_graph('#include "state.h"\nvoid publish(int input) { platform_owner = input; }\n',
                               {'state.h': 'extern int platform_owner;\n'})
        external = self.graph_nodes(graph, 'external_storage', 'platform_owner')
        source = self.graph_nodes(graph, 'storage', 'input')
        self.assertTrue(external and source and self.graph_reachable(graph, source, external))
        self.assertTrue(any(row['reason'] == 'external_storage_write_unresolved' for row in graph['unclassified']))
        target = next(n for n in graph['nodes'] if n['id'] in external)
        self.assertEqual(target['usr'], 'c:@platform_owner')

    def test_cpp_extern_redeclaration_does_not_hide_a_local_definition(self):
        graph = self.cpp_graph('extern int owner;\nint owner = 0;\nint read() { return owner; }\n')
        self.assertFalse(self.graph_nodes(graph, 'external_storage', 'owner'))
        self.assertEqual(len(self.graph_nodes(graph, 'storage', 'owner')), 1)

    def test_cpp_direct_reference_alias_write_reaches_original_storage(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'int choose() { int owner = 0; int &alias = owner; alias = platform_value(); return owner; }\n')
        source = self.graph_nodes(graph, 'CallExpr', 'platform_value()')
        target = self.graph_nodes(graph, 'return_slot', 'choose')
        self.assertTrue(self.graph_reachable(graph, source, target))
        self.assertTrue(any(row['kind'] == 'reference_alias' for row in graph['edges']))
        self.assertFalse(any(row['reason'] == 'reference_initialization_unresolved' for row in graph['unclassified']))

    def test_cpp_typedef_reference_chain_preserves_write_back(self):
        graph = self.cpp_graph('using Ref = int&;\nextern int platform_value();\n'
                               'int choose() { int owner = 0; Ref first = owner; Ref second = first; second = platform_value(); return owner; }\n')
        self.assertTrue(self.graph_reachable(graph,
                        self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                        self.graph_nodes(graph, 'return_slot', 'choose')))
        self.assertEqual(sum(e['kind'] == 'reference_alias' for e in graph['edges']), 4)

    def test_cpp_value_copy_does_not_become_a_reference_alias(self):
        graph = self.cpp_graph('extern int platform_value();\n'
                               'int choose() { int owner = 0; int copy = owner; copy = platform_value(); return owner; }\n')
        self.assertFalse(any(row['kind'] == 'reference_alias' for row in graph['edges']))
        self.assertFalse(self.graph_reachable(graph,
                         self.graph_nodes(graph, 'CallExpr', 'platform_value()'),
                         self.graph_nodes(graph, 'return_slot', 'choose')))

    def test_cpp_type_kind_uses_compiler_canonical_type_for_aliases(self):
        inventory = self.parse('using Ref = int&; using Callback = int(*)(int&);\n'
                               'void bind(int &value) { Ref alias = value; Callback callback = nullptr; }\n')
        alias = next(n for n in inventory['nodes'] if n['kind'] == 'VarDecl' and n['name'] == 'alias')
        callback = next(n for n in inventory['nodes'] if n['kind'] == 'VarDecl' and n['name'] == 'callback')
        self.assertEqual(alias['type_kind'], 'LValueReference')
        self.assertEqual(callback['type_kind'], 'Pointer')

    def test_cpp_external_field_declaration_is_not_assumed_platform_input(self):
        self.path.write_text('#include "object.h"\nint read(Object &object) { return object.owner; }\n')
        header = self.root / 'object.h'
        header.write_text('struct Object { int owner; };\n')
        inventory = self.reader.parse(self.path, [str(self.path)], self.argv)
        graph = self.verifier.CppInputFlowGraph([inventory], {str(self.path): self.path.read_bytes()}).build()
        field = next(n for n in graph['nodes'] if n['kind'] == 'external_storage' and n['label'] == 'Object::owner')
        self.assertEqual(field['declaration_kind'], 'FieldDecl')
        self.assertEqual(field['usr'], 'c:@S@Object@FI@owner')
        self.assertNotIn('input', field)
        self.assertTrue(self.graph_reachable(graph, {field['id']}, self.graph_nodes(graph, 'return_slot', 'read')))

    def test_cpp_graph_rejects_stale_input_and_bad_compiler_results(self):
        inventory = self.parse('int value() { return 1; }\n')
        with self.assertRaisesRegex(ValueError, '^lcer.source_inventory_invalid$'):
            self.verifier.CppInputFlowGraph([inventory], {str(self.path): b'int value() { return 2; }\n'})
        inventory['diagnostics'] = [{'severity': 3, 'message': 'actual parse failed'}]
        with self.assertRaisesRegex(ValueError, '^lcer.source_inventory_invalid$'):
            self.verifier.CppInputFlowGraph([inventory], {str(self.path): self.path.read_bytes()})

    def test_cpp_graph_dynamic_dispatch_and_pointer_effects_stay_unclassified(self):
        graph = self.cpp_graph('struct Base { virtual int read() = 0; };\n'
                               'int choose(Base &box, int *out) { *out = box.read(); return *out; }\n')
        reasons = {row['reason'] for row in graph['unclassified']}
        self.assertIn('dynamic_call_unresolved', reasons)
        self.assertIn('indirect_storage_target_unresolved', reasons)
        self.assertFalse(graph['source_audit_complete'])


class DecodedMemberTests(unittest.TestCase):
    def setUp(self):
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        self.verifier = verifier

    def graph(self, source):
        return self.verifier.PythonInputFlowGraph({'entry.py': source.encode()}).build()

    def decoder(self, source, owner='read'):
        graph = self.graph(source)
        return graph, [r for r in graph['json_decoded_member_inventory'] if graph['nodes'][r['node']]['function'] == owner]

    def pair_source(self, extra='', store='out[key] = member', initial='{}'):
        return ('import json\ndef pairs(items):\n    out='+initial+'\n'
                '    for key, member in items:\n        if key in out: raise ValueError("duplicate")\n'
                '        '+store+'\n'+extra+'    return out\n'
                'def read(raw): return json.loads(raw, object_pairs_hook=pairs)\n')

    def test_native_decoder_has_recursive_members_with_unaccepted_mutation_premise(self):
        graph, rows = self.decoder('import json\ndef read(raw): return json.loads(raw)\n')
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['status'], 'conditional_recursive_member_construction')
        self.assertEqual(row['recursive_grammar']['dict_members'], {'key': 'exact_str', 'value': 'recursive_value'})
        self.assertIn('json_reachable_decoded_members_stable_until_return', row['preconditions'])
        for flag in ('callback_effects_accepted', 'binding_stability_accepted', 'reachable_mutation_closure_accepted'):
            self.assertFalse(row[flag])
        self.assertFalse(graph['source_audit_complete'])

    def test_pair_builder_preserves_actual_key_and_member_producers(self):
        graph, rows = self.decoder(self.pair_source())
        self.assertEqual(len(rows), 1)
        hook = rows[0]['callback_constructors'][0]
        self.assertEqual(hook['kind'], 'fresh_dict_forwarding_decoded_pairs')
        self.assertEqual((hook['input_parameter'], hook['accumulator'], hook['key_parameter'], hook['member_parameter']),
                         ('items', 'out', 'key', 'member'))
        self.assertEqual(hook['member_origin'], 'native_decoded_pair_value')
        self.assertFalse(hook['input_members_modified_by_store'])
        self.assertTrue(any(r['reason'] == 'json_recursive_member_stability_summary_required' for r in graph['unclassified']))

    def test_actual_core_parser_callbacks_have_recursive_member_construction(self):
        source = (CONTRACT_PATH.parent / 'live_cross_domain_evidence_round_trip.py').read_text()
        graph, rows = self.decoder(source, 'parse_stored_json')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['status'], 'conditional_recursive_member_construction')
        self.assertEqual({r['kind'] for r in rows[0]['callback_constructors']},
                         {'fresh_dict_forwarding_decoded_pairs', 'no_successful_callback_return'})
        self.assertFalse(graph['source_audit_complete'])

    def test_actual_verifier_callbacks_bind_guard_and_native_float_calls(self):
        import ast
        source = (CONTRACT_PATH.parent / 'verify_live_cross_domain_evidence_round_trip_release.py').read_text()
        selected = [ast.get_source_segment(source, n) for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name in ('require', 'strict_json')]
        graph, rows = self.decoder('import json, math\n'+'\n'.join(selected)+'\n', 'strict_json')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['status'], 'conditional_recursive_member_construction')
        callbacks = {r['hook']: r for r in rows[0]['callback_constructors']}
        self.assertEqual(callbacks['object_pairs_hook']['guard']['kind'], 'successful_duplicate_guard')
        self.assertEqual(callbacks['parse_float']['kind'], 'native_scalar_conversion_with_finite_guard')
        self.assertTrue(any('json_member_guard_identity_and_body_stable:entry.py::require@' in p for p in rows[0]['preconditions']))

    def test_dict_return_type_does_not_hide_replaced_member_objects(self):
        source = 'class Hidden: pass\nreplacement=Hidden()\n'+self.pair_source(store='out[key] = replacement')
        graph, rows = self.decoder(source)
        self.assertEqual(len(rows), 1)
        self.assertIn('dict', rows[0]['root_types'])
        self.assertEqual(rows[0]['status'], 'callback_member_construction_unresolved')
        self.assertNotIn('recursive_grammar', rows[0])
        run = subprocess.run([sys.executable, '-B', '-c', source+'print(type(read("{\\"x\\":1}")["x"]).__name__)\n'],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), 'Hidden')

    def test_escaped_accumulator_and_extra_callback_effects_remain_unresolved(self):
        source = 'escaped=[]\n'+self.pair_source(extra='    escaped.append(out)\n')
        graph, rows = self.decoder(source)
        self.assertTrue(rows)
        self.assertEqual(rows[0]['status'], 'callback_member_construction_unresolved')
        self.assertFalse(graph['source_audit_complete'])

    def test_key_transform_and_reused_storage_do_not_claim_native_pair_forwarding(self):
        for source in [self.pair_source(store='out[key.upper()] = member'),
                       'CACHE={}\n'+self.pair_source(initial='CACHE'),
                       self.pair_source().replace('for key, member in items:', 'for key, key in items:')]:
            with self.subTest(source=source):
                graph, rows = self.decoder(source)
                self.assertTrue(rows)
                self.assertEqual(rows[0]['status'], 'callback_member_construction_unresolved')

    def test_guard_arguments_cannot_smuggle_the_accumulator_to_an_opaque_call(self):
        source=('def check(condition, value):\n    if not condition: raise ValueError(value)\n'+
                self.pair_source().replace('if key in out: raise ValueError("duplicate")', 'check(key not in out, out)'))
        _, rows = self.decoder(source)
        self.assertEqual(rows[0]['status'], 'callback_member_construction_unresolved')

    def test_pairs_hook_priority_does_not_require_an_ignored_object_hook_contract(self):
        source=self.pair_source().replace('def read(raw):', 'def ignored(value): return {"hidden":object()}\ndef read(raw):')
        source=source.replace('object_pairs_hook=pairs)', 'object_pairs_hook=pairs, object_hook=ignored)')
        _, rows = self.decoder(source)
        self.assertEqual(rows[0]['status'], 'conditional_recursive_member_construction')
        self.assertEqual([r['hook'] for r in rows[0]['callback_constructors']], ['object_pairs_hook'])

    def test_native_scalar_callback_preserves_leaf_type_and_binding_premise(self):
        _, rows = self.decoder('import json\ndef number(text): return float(text)\ndef read(raw): return json.loads(raw, parse_int=number)\n')
        self.assertEqual(rows[0]['status'], 'conditional_recursive_member_construction')
        callback=rows[0]['callback_constructors'][0]
        self.assertEqual((callback['kind'], callback['output_types']), ('native_scalar_conversion', ['float']))
        self.assertNotIn('int', rows[0]['recursive_grammar']['scalars'])
        self.assertIn('authentic_builtin_binding:float', rows[0]['preconditions'])

    def test_scalar_callback_cannot_inject_unclassified_nested_values(self):
        _, rows = self.decoder('import json\nforeign=object()\ndef number(text): return {"hidden":foreign}\ndef read(raw): return json.loads(raw, parse_int=number)\n')
        self.assertTrue(rows)
        self.assertEqual(rows[0]['status'], 'callback_member_construction_unresolved')

    def test_finite_guard_uses_resolved_api_identity_through_aliases(self):
        prefix=('import json\nimport math as numbers\n'
                'def require(condition):\n    if not condition: raise ValueError()\n')
        body=('def numeric(text):\n    value=float(text)\n    require(numbers.isfinite(value))\n    return value\n'
              'def read(raw): return json.loads(raw,parse_float=numeric)\n')
        _, rows = self.decoder(prefix+body)
        self.assertEqual(rows[0]['status'], 'conditional_recursive_member_construction')
        _, rows = self.decoder(prefix+'def replacement(value): return True\nnumbers.isfinite=replacement\n'+body)
        self.assertEqual(rows[0]['status'], 'callback_member_construction_unresolved')

    def test_external_member_write_tracks_module_alias_and_retains_replacement_target(self):
        source=('import json\nimport math as numbers\nalias=numbers\n'
                'def replacement(value): return True\nalias.isfinite=replacement\n'
                'def require(condition):\n    if not condition: raise ValueError()\n'
                'def numeric(text):\n    value=float(text)\n    require(numbers.isfinite(value))\n    return value\n'
                'def read(raw): return json.loads(raw,parse_float=numeric)\n')
        builder = self.verifier.PythonInputFlowGraph({'entry.py': source.encode()})
        graph = builder.build()
        calls = [c for c in builder.calls if builder.nodes[c['function']]['label'] == 'numbers.isfinite']
        self.assertEqual(len(calls), 1)
        references = builder._references()[calls[0]['function']]
        self.assertIn(('external', 'math.isfinite', ''), references)
        self.assertIn(('function', 'entry.py::replacement@4:0', ''), references)
        rows = [r for r in graph['json_decoded_member_inventory'] if graph['nodes'][r['node']]['function'] == 'read']
        self.assertEqual(rows[0]['status'], 'callback_member_construction_unresolved')
        self.assertFalse(graph['source_audit_complete'])

    def test_unrelated_external_member_writes_do_not_change_the_native_guard_target(self):
        prefix=('import json\nimport math as numbers\n'
                'def replacement(value): return True\n'
                'def require(condition):\n    if not condition: raise ValueError()\n')
        body=('def numeric(text):\n    value=float(text)\n    require(numbers.isfinite(value))\n    return value\n'
              'def read(raw): return json.loads(raw,parse_float=numeric)\n')
        for assignment in ('json.isfinite=replacement\n', 'numbers.unrelated=replacement\n'):
            with self.subTest(assignment=assignment):
                graph, rows = self.decoder(prefix+assignment+body)
                self.assertEqual(rows[0]['status'], 'conditional_recursive_member_construction')
                self.assertFalse(rows[0]['binding_stability_accepted'])
                self.assertFalse(graph['source_audit_complete'])

    def test_nonreturning_hook_adds_no_successful_member_and_keeps_effects_unaccepted(self):
        source='import json\neffects=[]\ndef reject(text):\n    effects.append(text)\n    raise ValueError(text)\ndef read(raw): return json.loads(raw, parse_int=reject)\n'
        _, rows = self.decoder(source)
        self.assertEqual(rows[0]['status'], 'conditional_recursive_member_construction')
        self.assertEqual(rows[0]['callback_constructors'][0]['kind'], 'no_successful_callback_return')
        self.assertFalse(rows[0]['callback_constructors'][0]['callback_effects_accepted'])
        self.assertNotIn('int', rows[0]['recursive_grammar']['scalars'])

    def test_member_construction_edges_do_not_propagate_callable_identity(self):
        graph, rows = self.decoder(self.pair_source())
        edges=[e for e in graph['edges'] if e['kind']=='json_decoded_member_construction_control']
        self.assertTrue(edges)
        self.assertTrue(all(e['reference'] is False for e in edges))
        for row in rows:
            self.assertEqual({e['source'] for e in edges if e['target']==row['node']}, set(row['inputs']))


class ClosedConstructorTests(unittest.TestCase):
    def setUp(self):
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        self.verifier = verifier

    def trace(self, source, name='make'):
        import ast
        raw = source.encode() if type(source) is str else source
        syntax = ast.parse(raw)
        function = next(n for n in syntax.body if isinstance(n, ast.FunctionDef) and n.name == name)
        return self.verifier.PythonClosedConstructor({'entry.py': raw}).trace(
            'entry.py::%s@%d:%d' % (name, function.lineno, function.col_offset))

    def initialize_module(self, source):
        raw = source.encode() if type(source) is str else source
        result = self.verifier.PythonModuleInitialization({'entry.py': raw}).analyze('entry.py')
        self.assertEqual(result['contract'], 'python_module_initialization.v1')
        self.assertEqual(result['source_sha256'], hashlib.sha256(raw).hexdigest())
        for name in ('source_executed', 'module_initialization_accepted', 'binding_stability_accepted',
                     'global_mutation_closure_accepted', 'source_audit_complete'):
            self.assertIs(result[name], False)
        return result

    def bind_constructor_initialization(self, source, name='make'):
        raw = source.encode() if type(source) is str else source
        trace = self.trace(raw, name)
        initialized = self.initialize_module(raw)
        return self.verifier.PythonConstructorInitialization({'entry.py': raw}).bind(trace, initialized)

    def constructor_value_stability(self, source, name='make'):
        raw = source.encode() if type(source) is str else source
        trace = self.trace(raw, name)
        initialized = self.initialize_module(raw)
        binding = self.bind_constructor_initialization(raw, name)
        return self.verifier.PythonConstructorValueStability({'entry.py': raw}).analyze(trace, initialized, binding)

    def comparison_dependencies(self, source):
        sources = {'entry.py': source.encode()}
        graph = self.verifier.PythonInputFlowGraph(sources).build()
        rows = [row for row in graph['context_dictionary_comparison_inventory'] if '::check@' in row['function']]
        self.assertTrue(rows)
        return sources, graph, rows

    def original_comparisons(self, rows):
        original = json.loads(json.dumps(rows))
        for row in original:
            row['contract'] = 'python_context_dictionary_comparison.v1'
            row['preconditions'] = row.pop('unrefined_preconditions')
            for operand in row['operands']:
                operand['preconditions'] = operand.pop('unrefined_preconditions')
                operand.pop('constructor_dependency_updates')
        return original

    def test_comparison_uses_initialized_scalars_and_keeps_table_binding_and_context(self):
        source = ('VALUE="A"\nTABLE={"owner":VALUE}\ndef factory(): return TABLE\n'
                  'def check(record): return record == factory()\ndef entry(): return check({})\n')
        _, graph, rows = self.comparison_dependencies(source)
        for row in rows:
            self.assertEqual(row['contract'], 'python_context_dictionary_comparison.v2')
            removed = 'constructor_global_value_graph_stable:entry.py:VALUE'
            self.assertIn(removed, row['unrefined_preconditions'])
            self.assertNotIn(removed, row['preconditions'])
            self.assertNotIn('constructor_module_initial_value_matches_declaration:entry.py:TABLE', row['preconditions'])
            for premise in ['constructor_module_binding_stable:entry.py:VALUE',
                            'constructor_module_binding_stable:entry.py:TABLE',
                            'constructor_global_value_graph_stable:entry.py:TABLE',
                            'authentic_python_builtin_immutable_scalar_semantics']:
                self.assertIn(premise, row['preconditions'])
            context = graph['call_context_closure']['contexts'][row['context']]
            self.assertEqual(row['required_condition_set'], context['required_condition_set'])
            for operand in row['operands']:
                self.assertTrue(set(operand['non_constructor_preconditions']) <= set(operand['preconditions']))
            self.assertFalse(row['member_effects_accepted'])
        self.assertFalse(graph['source_audit_complete'])

    def test_comparison_keeps_unresolved_initializer_and_later_rebinding_dependencies(self):
        for change in ('ALIAS=TABLE\nALIAS["owner"]="B"\n',
                       'def change():\n    global TABLE\n    TABLE={"owner":"B"}\n'):
            source = ('VALUE="A"\nTABLE={"owner":VALUE}\n'+change+
                      'def factory(): return TABLE\ndef check(record): return record == factory()\n'
                      'def entry(): return check({})\n')
            _, graph, rows = self.comparison_dependencies(source)
            for row in rows:
                self.assertIn('constructor_module_binding_stable:entry.py:TABLE', row['preconditions'])
                self.assertIn('constructor_global_value_graph_stable:entry.py:TABLE', row['preconditions'])
                if change.startswith('ALIAS'):
                    self.assertEqual(row['preconditions'], row['unrefined_preconditions'])
                self.assertFalse(row['operand_evaluation_effects_accepted'])

    def test_comparison_preserves_a_substituted_premise_with_another_origin(self):
        source = ('VALUE="A"\ndef factory(): return {"owner":VALUE}\n'
                  'def check(record): return record == factory()\ndef entry(): return check({})\n')
        sources, graph, rows = self.comparison_dependencies(source)
        original = self.original_comparisons(rows)
        retained = 'constructor_global_value_graph_stable:entry.py:VALUE'
        for row in original:
            operand = row['operands'][1]
            operand['non_constructor_preconditions'] = sorted(set(operand['non_constructor_preconditions']) | {retained})
        bound = self.verifier.PythonConstructorComparisonDependencies(sources).bind(
            original, graph['closed_constructor_inventory'], graph['module_initialization_inventory'],
            graph['constructor_initialization_inventory'], graph['constructor_value_stability_inventory'])
        self.assertTrue(all(retained in row['preconditions'] for row in bound))

    def test_comparison_chain_keeps_unresolved_constructor_effects(self):
        source = ('import os\nVALUE="A"\ndef fixed(): return {"owner":VALUE}\n'
                  'def external(): return {"owner":os.getenv("CITY_OWNER")}\n'
                  'def check(record): return record == fixed() == external()\ndef entry(): return check({})\n')
        _, graph, rows = self.comparison_dependencies(source)
        all_updates = [update for row in rows for operand in row['operands']
                       for update in operand['constructor_dependency_updates']]
        self.assertTrue(any(update['status']=='unresolved' for update in all_updates))
        for row in rows:
            updates = [update for operand in row['operands'] for update in operand['constructor_dependency_updates']]
            self.assertTrue(any(update['substituted_preconditions'] for update in updates))
            for update in updates:
                if update['status']=='unresolved':
                    self.assertEqual(update['remaining_preconditions'], update['original_preconditions'])
                    self.assertTrue(set(update['remaining_preconditions']) <= set(row['preconditions']))
            self.assertFalse(row['member_effects_accepted'])

    def test_comparison_dependencies_reject_replaced_binding_and_stability_records(self):
        source = ('VALUE="A"\ndef factory(): return {"owner":VALUE}\n'
                  'def check(record): return record == factory()\ndef entry(): return check({})\n')
        sources, graph, rows = self.comparison_dependencies(source)
        for target, code in [('constructor_initialization_inventory','constructor_comparison_binding_mismatch'),
                             ('constructor_value_stability_inventory','constructor_comparison_stability_mismatch')]:
            altered = json.loads(json.dumps(graph[target])); altered[0]['remaining_preconditions']=[]
            inputs = {name: graph[name] for name in ['constructor_initialization_inventory','constructor_value_stability_inventory']}
            inputs[target] = altered
            with self.assertRaisesRegex(ValueError, '^'+code+'$'):
                self.verifier.PythonConstructorComparisonDependencies(sources).bind(
                    self.original_comparisons(rows), graph['closed_constructor_inventory'], graph['module_initialization_inventory'],
                    inputs['constructor_initialization_inventory'], inputs['constructor_value_stability_inventory'])

    def test_comparison_dependencies_reject_lost_operand_provenance_or_false_constructor_identity(self):
        source = ('VALUE="A"\ndef factory(): return {"owner":VALUE}\n'
                  'def check(record): return record == factory()\ndef entry(): return check({})\n')
        sources, graph, rows = self.comparison_dependencies(source)
        for field, value, code in [('non_constructor_preconditions',[], 'constructor_comparison_operand_provenance'),
                                   ('constructor_proofs',[True], 'constructor_comparison_operand_membership')]:
            original = self.original_comparisons(rows); original[0]['operands'][1][field]=value
            with self.assertRaisesRegex(ValueError, '^'+code+'$'):
                self.verifier.PythonConstructorComparisonDependencies(sources).bind(
                    original, graph['closed_constructor_inventory'], graph['module_initialization_inventory'],
                    graph['constructor_initialization_inventory'], graph['constructor_value_stability_inventory'])

    def test_constructor_value_stability_separates_actual_scalars_from_table(self):
        raw = (CONTRACT_PATH.parent / 'concurrent_external_evidence_arbitration.py').read_bytes()
        row = self.constructor_value_stability(raw, 'initial_canonical_envelope')
        self.assertEqual(row['status'], 'conditional_immutable_contents')
        self.assertEqual(len(row['immutable_globals']), 11)
        self.assertEqual([r['name'] for r in row['mutable_globals']], ['DOMAIN_TABLE'])
        self.assertEqual(len(row['substituted_preconditions']), 11)
        self.assertEqual(len(row['remaining_preconditions']), 24)
        for value in row['immutable_globals'] + row['mutable_globals']:
            self.assertIn(value['binding_precondition'], row['remaining_preconditions'])
        self.assertIn(row['mutable_globals'][0]['content_precondition'], row['remaining_preconditions'])
        self.assertEqual(row['replacement_preconditions'], ['authentic_python_builtin_immutable_scalar_semantics'])

    def test_constructor_value_stability_keeps_exact_scalar_types_and_alias_names(self):
        source = 'TEXT="A"\nCOPY=TEXT\nNUMBER=1\nFLAG=True\nEMPTY=None\ndef make(): return [COPY,NUMBER,FLAG,EMPTY]\n'
        row = self.constructor_value_stability(source)
        values = {r['name']: r['initial_value'] for r in row['immutable_globals']}
        self.assertEqual(values['TEXT'], values['COPY'])
        self.assertEqual(values['NUMBER'], {'type': 'int', 'value': 1})
        self.assertEqual(values['FLAG'], {'type': 'bool', 'value': True})
        self.assertEqual(values['EMPTY'], {'type': 'NoneType', 'value': None})
        self.assertEqual(len(row['immutable_globals']), 5)
        self.assertEqual(row['mutable_globals'], [])

    def test_constructor_value_stability_does_not_treat_containers_as_scalars(self):
        for literal in ('{"owner":"A"}', '["A"]'):
            with self.subTest(literal=literal):
                row = self.constructor_value_stability('VALUE=' + literal + '\ndef make(): return VALUE\n')
                self.assertEqual(row['status'], 'mutable_contents_unresolved')
                self.assertEqual(row['immutable_globals'], [])
                self.assertEqual(row['substituted_preconditions'], [])
                self.assertEqual(row['replacement_preconditions'], [])
                self.assertIn('constructor_global_value_graph_stable:entry.py:VALUE', row['remaining_preconditions'])
        row = self.constructor_value_stability('VALUE=(["A"],)\ndef make(): return VALUE\n')
        self.assertEqual(row['status'], 'unresolved')
        self.assertEqual(row['substituted_preconditions'], [])

    def test_constructor_value_stability_does_not_discharge_module_rebinding(self):
        source = 'VALUE="A"\ndef make(): return VALUE\ndef change():\n    global VALUE\n    VALUE="B"\n'
        row = self.constructor_value_stability(source)
        self.assertEqual(row['status'], 'conditional_immutable_contents')
        self.assertIn('constructor_module_binding_stable:entry.py:VALUE', row['remaining_preconditions'])
        for name in ('source_executed', 'binding_stability_accepted', 'global_mutation_closure_accepted',
                     'global_obligations_removed', 'source_audit_complete'):
            self.assertIs(row[name], False)

    def test_constructor_value_stability_rejects_forged_binding_and_scalar_tags(self):
        source = 'VALUE={"owner":"A"}\ndef make(): return VALUE\n'
        trace, initialized = self.trace(source), self.initialize_module(source)
        binding = self.bind_constructor_initialization(source)
        reader = self.verifier.PythonConstructorValueStability({'entry.py': source.encode()})
        for mutate in (lambda row: row['global_reads'][0].update(value={'type': 'str', 'value': 'A'}),
                       lambda row: row.update(remaining_preconditions=[]),
                       lambda row: row.update(source_audit_complete=True)):
            altered = json.loads(json.dumps(binding)); mutate(altered)
            result = reader.analyze(trace, initialized, altered)
            self.assertEqual(result['status'], 'unresolved')
            self.assertEqual(result['reason'], 'constructor_value_stability_binding_mismatch')
            self.assertEqual(result['substituted_preconditions'], [])

    def test_constructor_value_stability_is_emitted_by_actual_graph_path(self):
        source = 'VALUE="A"\nTABLE={"owner":VALUE}\ndef expected(): return TABLE\n'
        source += 'def check(record): return record == expected()\ndef root(): return check({})\n'
        graph = self.verifier.PythonInputFlowGraph({'entry.py': source.encode()}).build()
        rows = graph['constructor_value_stability_inventory']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['status'], 'conditional_immutable_contents')
        self.assertEqual([r['name'] for r in rows[0]['immutable_globals']], ['VALUE'])
        self.assertEqual([r['name'] for r in rows[0]['mutable_globals']], ['TABLE'])
        self.assertFalse(graph['source_audit_complete'])

    def test_constructor_initialization_binds_actual_canonical_reads(self):
        raw = (CONTRACT_PATH.parent / 'concurrent_external_evidence_arbitration.py').read_bytes()
        trace = self.trace(raw, 'initial_canonical_envelope')
        row = self.bind_constructor_initialization(raw, 'initial_canonical_envelope')
        self.assertEqual(row['status'], 'conditional_initial_values_bound')
        names = {r['name'] for r in row['global_reads']}
        self.assertIn('DOMAIN_TABLE', names)
        self.assertEqual({r['name'] for r in row['callable_bindings']},
                         {'_identity', '_contract', 'initial_canonical_envelope'})
        self.assertEqual(set(row['substituted_preconditions']),
                         {p for p in trace['preconditions'] if p.startswith('constructor_module_initial_value_matches_declaration:')})
        self.assertTrue(all(p in row['remaining_preconditions'] for p in trace['preconditions']
                            if not p.startswith('constructor_module_initial_value_matches_declaration:')))
        self.assertIn('authentic_native_exception_base:ValueError', row['replacement_preconditions'])
        self.assertFalse(row['source_audit_complete'])

    def test_constructor_initialization_rejects_mutation_after_literal_declaration(self):
        source = 'TABLE={"owner":"A"}\nALIAS=TABLE\nALIAS["owner"]="B"\ndef make(): return TABLE\n'
        self.assertEqual(self.trace(source)['status'], 'conditional_closed_builtin_tree')
        row = self.bind_constructor_initialization(source)
        self.assertEqual(row['status'], 'unresolved')
        self.assertEqual(row['reason'], 'constructor_initialization_module_unresolved')
        self.assertEqual(row['substituted_preconditions'], [])

    def test_constructor_initialization_rejects_forward_module_read(self):
        source = 'ALIAS=TABLE\nTABLE={"owner":"A"}\ndef make(): return ALIAS\n'
        self.assertEqual(self.trace(source)['status'], 'conditional_closed_builtin_tree')
        row = self.bind_constructor_initialization(source)
        self.assertEqual(row['status'], 'unresolved')
        self.assertEqual(row['reason'], 'constructor_initialization_module_unresolved')

    def test_constructor_initialization_authenticates_both_records(self):
        source = 'TABLE={"owner":"A"}\ndef make(): return TABLE\n'
        trace, initialized = self.trace(source), self.initialize_module(source)
        binder = self.verifier.PythonConstructorInitialization({'entry.py': source.encode()})
        altered_trace = json.loads(json.dumps(trace))
        altered_trace['nodes'][0]['literal'] = 'changed'
        self.assertEqual(binder.bind(altered_trace, initialized)['reason'], 'constructor_initialization_trace_mismatch')
        altered_initializer = json.loads(json.dumps(initialized))
        altered_initializer['values']['TABLE']['items'][0][1]['value'] = 'B'
        self.assertEqual(binder.bind(trace, altered_initializer)['reason'], 'constructor_initialization_record_mismatch')
        self.assertEqual(binder.bind(trace, None)['reason'], 'constructor_initialization_record_missing')

    def test_constructor_initialization_retains_later_mutation_and_binding_obligations(self):
        source = 'TABLE={"owner":"A"}\ndef make(): return TABLE\ndef change(): TABLE["owner"]="B"\n'
        row = self.bind_constructor_initialization(source)
        self.assertEqual(row['status'], 'conditional_initial_values_bound')
        self.assertIn('constructor_global_value_graph_stable:entry.py:TABLE', row['remaining_preconditions'])
        self.assertIn('constructor_module_binding_stable:entry.py:TABLE', row['remaining_preconditions'])
        for name in ('module_initialization_accepted', 'binding_stability_accepted',
                     'global_mutation_closure_accepted', 'global_obligations_removed', 'source_audit_complete'):
            self.assertIs(row[name], False)

    def test_constructor_initialization_is_emitted_by_actual_graph_path(self):
        source = 'TABLE={"owner":"A"}\ndef expected(): return TABLE\ndef check(record): return record == expected()\n'
        for suffix, status in [('check({})\n', 'unresolved'),
                               ('def root(): return check({})\n', 'conditional_initial_values_bound')]:
            with self.subTest(status=status):
                graph = self.verifier.PythonInputFlowGraph({'entry.py': (source + suffix).encode()}).build()
                rows = graph['constructor_initialization_inventory']
                self.assertTrue(rows)
                self.assertEqual(rows[0]['status'], status)
                self.assertFalse(graph['source_audit_complete'])

    def test_module_initialization_tracks_actual_frozen_table_and_reverse_lookup(self):
        raw = (CONTRACT_PATH.parent / 'concurrent_external_evidence_arbitration.py').read_bytes()
        result = self.initialize_module(raw)
        self.assertEqual(result['status'], 'conditional_initialized_values')
        table = dict(result['values']['DOMAIN_TABLE']['items'])
        self.assertEqual(set(table), {'domain_A', 'domain_B'})
        self.assertEqual(result['values']['INPUT_TO_DOMAIN'], {'type': 'dict', 'items': [
            ['physical_allocate_shared_slot_A_0001', {'type': 'str', 'value': 'domain_A'}],
            ['physical_allocate_shared_slot_B_0001', {'type': 'str', 'value': 'domain_B'}]]})
        self.assertEqual(result['events'][-1]['operation'], 'inactive_main_guard')
        self.assertIn('normal_import_name_not_main:entry.py', result['preconditions'])
        self.assertIn('authentic_native_exception_base:ValueError', result['preconditions'])

    def test_module_initialization_rejects_forward_reads_and_rebindings(self):
        for source, reason in [
            ('COPY=TABLE\nTABLE={"A":"owner"}\n', 'value_not_initialized:TABLE'),
            ('TABLE={"A":"owner"}\nTABLE={"B":"other"}\n', 'binding_replaced:TABLE'),
            ('__name__="__main__"\n', 'binding_replaced:__name__'),
            ('import json\njson=1\n', 'binding_replaced:json')]:
            with self.subTest(reason=reason):
                result = self.initialize_module(source)
                self.assertEqual(result['status'], 'unresolved')
                self.assertEqual(result['reason'], 'module_initialization_' + reason)

    def test_module_initialization_rejects_top_level_mutation_and_late_import(self):
        for suffix, reason in [('TABLE.clear()\n', 'statement_unclassified:Expr'),
                               ('ALIAS=TABLE\nALIAS["A"]="B"\n', 'assignment_shape'),
                               ('import os\n', 'late_import_effects')]:
            with self.subTest(suffix=suffix):
                result = self.initialize_module('TABLE={"A":"owner"}\n' + suffix)
                self.assertEqual(result['status'], 'unresolved')
                self.assertEqual(result['reason'], 'module_initialization_' + reason)
                self.assertNotIn('values', result)

    def test_module_initialization_checks_defaults_decorators_and_annotations(self):
        sources = [('@decorate\ndef f(): pass\n', 'decorator_effects'),
                   ('def f(value=mutate()): pass\n', 'expression_unclassified:Call'),
                   ('def f(value: mutate()): pass\n', 'annotation_effects'),
                   ('TABLE: mutate()={"A":"owner"}\n', 'annotation_effects')]
        for source, reason in sources:
            with self.subTest(reason=reason):
                self.assertEqual(self.initialize_module(source)['reason'], 'module_initialization_' + reason)
        accepted = self.initialize_module('from __future__ import annotations\nTABLE={"A":"owner"}\n'
                                          'def f(value: mutate()=TABLE) -> mutate():\n    TABLE.clear()\n')
        self.assertEqual(accepted['status'], 'conditional_initialized_values')
        self.assertEqual(accepted['events'][-1]['body_execution'], 'deferred')
        self.assertEqual(accepted['events'][-1]['defaults'], [accepted['values']['TABLE']])

    def test_module_initialization_keeps_comprehension_scope_and_exact_builtin_rules(self):
        result = self.initialize_module('TABLE={"A":{"id":"one"},"B":{"id":"two"}}\n'
                                        'REVERSE={row["id"]:name for name,row in TABLE.items()}\n')
        self.assertEqual(result['status'], 'conditional_initialized_values')
        self.assertEqual(result['values']['REVERSE']['items'], [
            ['one', {'type': 'str', 'value': 'A'}], ['two', {'type': 'str', 'value': 'B'}]])
        self.assertNotIn('row', result['values'])
        for source in ['TABLE={"A":"x","B":"x"}\nX={v:k for k,v in TABLE.items()}\n',
                       'TABLE={"A":"x"}\nX={v:k for k,v in TABLE.items() if predicate(v)}\n',
                       'TABLE=[]\nX={v:k for k,v in TABLE.items()}\n']:
            with self.subTest(source=source):
                self.assertEqual(self.initialize_module(source)['status'], 'unresolved')

    def test_module_initialization_separates_exception_bases_and_inactive_main(self):
        accepted = self.initialize_module('class Rejected(ValueError):\n    pass\n'
                                          'VALUE=("A",None)\nif __name__ == "__main__":\n    mutate()\n')
        self.assertEqual(accepted['status'], 'conditional_initialized_values')
        self.assertEqual(accepted['values']['VALUE']['type'], 'tuple')
        for source in ['ValueError=1\nclass Rejected(ValueError): pass\n',
                       'class Rejected(ValueError):\n    mutate()\n',
                       'class Rejected(ValueError, metaclass=Other): pass\n',
                       'if __name__ == "__main__":\n    pass\nelse:\n    mutate()\n',
                       'if choose():\n    VALUE=1\n']:
            with self.subTest(source=source):
                self.assertEqual(self.initialize_module(source)['status'], 'unresolved')

    def test_actual_canonical_factory_members_match_frozen_r0(self):
        import ast
        path = 'proof_kernel/concurrent_external_evidence_arbitration.py'
        raw = (CONTRACT_PATH.parent / 'concurrent_external_evidence_arbitration.py').read_bytes()
        proof = self.verifier.PythonClosedConstructor({path: raw}).trace(
            path + '::initial_canonical_envelope@225:0')
        expected = json.loads((CONTRACT_PATH.parent / 'ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R0.json').read_bytes())
        self.assertEqual(proof['status'], 'conditional_closed_builtin_tree')
        self.assertEqual(proof['value'], expected)
        self.assertEqual(proof['source_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertFalse(proof['source_executed'])
        self.assertFalse(proof['binding_stability_accepted'])
        self.assertFalse(proof['global_mutation_closure_accepted'])
        self.assertIn('constructor_global_value_graph_stable:' + path + ':DOMAIN_TABLE', proof['preconditions'])
        self.assertEqual({r['function'] for r in proof['nodes'] if r['operation'] == 'function_return'},
                         {'_identity', '_contract', 'initial_canonical_envelope'})
        positions = {(n.lineno, n.col_offset, n.end_lineno, n.end_col_offset)
                     for n in ast.walk(ast.parse(raw)) if hasattr(n, 'lineno')}
        for row in proof['nodes']:
            source = row['source']
            self.assertEqual(source['path'], path)
            self.assertIn((source['line'], source['column'], source['end_line'], source['end_column']), positions)
            self.assertTrue(all(i < row['id'] for i in row['inputs']))

    def test_nested_literal_helpers_keep_member_and_lookup_producers(self):
        proof = self.trace('TABLE={"A":{"owner":"domain_A"}}\n'
                           'def row(domain):\n    selected=TABLE[domain]\n    return {"owner":selected["owner"]}\n'
                           'def make():\n    return {"result":row("A"),"pending":[],"parent":None}\n')
        self.assertEqual(proof['value'], {'result': {'owner': 'domain_A'}, 'pending': [], 'parent': None})
        self.assertEqual(sum(r['operation'] == 'dictionary_lookup' for r in proof['nodes']), 2)
        self.assertTrue(any(r['operation'] == 'local_read' and r['name'] == 'domain' for r in proof['nodes']))
        self.assertIn('constructor_native_exact_dict_string_lookup', proof['preconditions'])

    def test_external_callback_is_not_executed_or_accepted(self):
        proof = self.trace('from os import getenv\ndef make():\n    return {"owner":getenv("CITY_OWNER")}\n')
        self.assertEqual(proof['status'], 'unresolved')
        self.assertEqual(proof['reason'], 'constructor_callable_unresolved:getenv')
        self.assertNotIn('value', proof)
        self.assertFalse(proof['source_executed'])

    def test_container_mutation_and_arbitrary_statements_refuse(self):
        for statement in ['value["owner"]="changed"', 'value.update({"owner":"changed"})',
                          'for item in []:\n        pass', 'global value']:
            with self.subTest(statement=statement):
                proof = self.trace('value={}\ndef make():\n    '+statement+'\n    return value\n')
                self.assertEqual(proof['status'], 'unresolved')
                self.assertNotIn('value', proof)

    def test_recursive_call_and_global_cycles_remain_unresolved(self):
        for source, reason in [('def make():\n    return make()\n', 'constructor_recursion_unresolved:make'),
                               ('A=B\nB=A\ndef make():\n    return A\n', 'constructor_recursive_global:A')]:
            proof = self.trace(source)
            self.assertEqual((proof['status'], proof['reason']), ('unresolved', reason))

    def test_rebound_module_symbol_never_chooses_a_convenient_definition(self):
        proof = self.trace('VALUE={}\nVALUE={"owner":"other"}\ndef make():\n    return VALUE\n')
        self.assertEqual(proof['status'], 'unresolved')
        self.assertEqual(proof['reason'], 'constructor_binding_missing_or_ambiguous:VALUE')

    def test_unreachable_binding_still_controls_local_scope(self):
        proof = self.trace('VALUE={}\ndef make():\n    return VALUE\n    VALUE=[]\n')
        self.assertEqual(proof['reason'], 'constructor_unbound_local:VALUE')
        proof = self.trace('def helper(): return {}\ndef make():\n    return helper()\n    def helper(): return []\n')
        self.assertEqual(proof['status'], 'unresolved')
        self.assertEqual(proof['reason'], 'constructor_statement_unresolved:FunctionDef')

    def test_global_alias_keeps_storage_stability_obligation(self):
        proof = self.trace('VALUE={"items":[]}\ndef make():\n    return {"left":VALUE,"right":VALUE}\n')
        self.assertEqual(proof['value'], {'left': {'items': []}, 'right': {'items': []}})
        reads = [r for r in proof['nodes'] if r['operation'] == 'global_read' and r['name'] == 'VALUE']
        self.assertEqual(len(reads), 2)
        self.assertEqual(reads[0]['inputs'], reads[1]['inputs'])
        self.assertIn('constructor_global_value_graph_stable:entry.py:VALUE', proof['preconditions'])
        self.assertFalse(proof['global_mutation_closure_accepted'])

    def test_annotation_execution_is_separate_from_deferred_source(self):
        source='VALUE:dict={"x":None}\ndef make()->dict:\n    return VALUE\n'
        self.assertEqual(self.trace(source)['status'], 'unresolved')
        self.assertEqual(self.trace('from __future__ import annotations\n'+source)['status'],
                         'conditional_closed_builtin_tree')

    def test_module_mutation_can_invalidate_the_constructor_initial_value_premise(self):
        source='VALUE={"owner":"original"}\nVALUE["owner"]="changed"\ndef make(): return VALUE\n'
        run = subprocess.run([sys.executable, '-B', '-c', source+'print(make()["owner"])\n'],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), 'changed')
        proof = self.trace(source)
        self.assertEqual(proof['value'], {'owner': 'original'})
        self.assertIn('constructor_module_initial_value_matches_declaration:entry.py:VALUE', proof['preconditions'])
        self.assertFalse(proof['module_initialization_accepted'])
        self.assertFalse(proof['global_mutation_closure_accepted'])

    def test_unsupported_argument_binding_is_never_filled_from_defaults(self):
        for source in ['def make(x={}): return x\n',
                       'def helper(x): return x\ndef make(): return helper(x={})\n',
                       'def helper(x): return x\ndef make(): return helper(*[{}])\n']:
            self.assertEqual(self.trace(source)['status'], 'unresolved')

    def test_function_coordinate_must_match_actual_source(self):
        proof = self.verifier.PythonClosedConstructor({'entry.py': b'def make(): return {}\n'}).trace('entry.py::make@2:0')
        self.assertEqual(proof['status'], 'unresolved')
        self.assertEqual(proof['reason'], 'constructor_root_source_mismatch')

    def test_unsupported_keys_and_receivers_do_not_become_closed_members(self):
        for value in ['{1: "value"}', '{"x":None,"x":False}', '[1][0]', '{"x":1}["missing"]', '1.5']:
            with self.subTest(value=value):
                self.assertEqual(self.trace('def make(): return '+value+'\n')['status'], 'unresolved')

    def test_dictionary_context_uses_factory_trace_without_accepting_effects(self):
        source=('def factory(): return {"members":["member",None]}\n'
                'def check(record): return record != factory()\ncheck({})\n')
        graph = self.verifier.PythonInputFlowGraph({'entry.py': source.encode()}).build()
        proof = next(r for r in graph['closed_constructor_inventory'] if '::factory@' in r['function'])
        self.assertEqual(proof['value'], {'members': ['member', None]})
        comparisons = [r for r in graph['context_dictionary_comparison_inventory'] if '::check@' in r['function']]
        self.assertTrue(comparisons)
        for row in comparisons:
            self.assertIn(proof['id'], row['operands'][1]['constructor_proofs'])
            self.assertTrue(set(proof['preconditions']) <= set(row['preconditions']))
            self.assertFalse(row['member_effects_accepted'])
        self.assertFalse(graph['source_audit_complete'])

    def test_platform_input_in_factory_remains_an_unresolved_member(self):
        source=('import os\ndef factory(): return {"owner":os.getenv("CITY_OWNER")}\n'
                'def check(record): return record != factory()\ncheck({})\n')
        graph = self.verifier.PythonInputFlowGraph({'entry.py': source.encode()}).build()
        proof = next(r for r in graph['closed_constructor_inventory'] if '::factory@' in r['function'])
        self.assertEqual(proof['status'], 'unresolved')
        self.assertNotIn('value', proof)
        self.assertFalse(graph['source_audit_complete'])


class PythonInputFlowTests(unittest.TestCase):
    """Offline source fixtures exercise graph derivation, not audit acceptance."""

    def graph(self, sources):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as bootstrap
        sys.path[:] = previous
        return bootstrap.PythonInputFlowGraph(
            {'proof_kernel/' + name + '.py': source.encode('utf-8') for name, source in sources.items()}).build()

    def nodes(self, graph, kind=None, label=None, function=None):
        return {node['id'] for node in graph['nodes'] if (kind is None or node['kind'] == kind)
                and (label is None or node['label'] == label)
                and (function is None or node['function'] == function)}

    def reachable(self, graph, starts, ends):
        visited, pending = set(), list(starts)
        outgoing = {}
        for edge in graph['edges']:
            outgoing.setdefault(edge['source'], set()).add(edge['target'])
        while pending:
            node = pending.pop()
            if node in ends:
                return True
            if node not in visited:
                visited.add(node)
                pending.extend(outgoing.get(node, ()))
        return False

    def return_inventory(self, graph, function):
        return next(row for row in graph['function_return_inventory'] if '::' + function + '@' in row['function'])

    def test_compiler_scope_rejection_remains_an_explicit_audit_failure(self):
        with mock.patch('symtable.symtable', side_effect=SyntaxError('compiler rejection')):
            graph = self.graph({'entry': 'def f():return 1\n'})
        self.assertIn('native_compiler_scope_rejected', {r['reason'] for r in graph['unclassified']})
        self.assertEqual(len(self.nodes(graph, kind='function_definition')), 1)
        self.assertTrue(self.nodes(graph, kind='compiler_scope_rejection'))

    def test_implicit_class_cell_is_separate_from_the_class_dictionary(self):
        graph = self.graph({'entry': 'class C:\n __class__=7\n def value(self):return __class__\n'})
        cell = graph['implicit_class_cell_inventory'][0]
        self.assertEqual(graph['nodes'][cell['node']]['kind'], 'implicit_class_cell')
        self.assertNotIn(cell['node'], self.nodes(graph, kind='symbol', label='__class__'))
        captured = next(r for r in graph['function_environment_inventory']['functions'] if '::C.value@' in r['function'])
        self.assertEqual([r['symbol'] for r in captured['closure_cells']], [cell['node']])
        self.assertFalse(cell['publication_effects_accepted'])

    def test_implicit_class_cell_crosses_nested_function_scopes(self):
        graph = self.graph({'entry': 'class C:\n def outer(self):\n  def middle():\n   return lambda: __class__\n  return middle\n'})
        cell = graph['implicit_class_cell_inventory'][0]['node']
        rows = graph['function_environment_inventory']['functions']
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(cell in r['capture_nodes'] for r in rows))

    def test_class_cell_shadowing_and_global_declarations_do_not_capture_the_class(self):
        graph = self.graph({'entry': '__class__=1\nclass C:\n def parameter(self,__class__):return __class__\n def global_name(self):\n  global __class__\n  return __class__\n'})
        self.assertEqual(graph['implicit_class_cell_inventory'], [])
        self.assertTrue(all(not r['closure_cells'] for r in graph['function_environment_inventory']['functions']))

    def test_zero_argument_super_connects_inherited_body_and_original_receiver(self):
        graph = self.graph({'entry': 'class A:\n def f(self,x):return x\nclass B(A):\n def f(self,x):return super().f(x)\nB().f(7)\n'})
        calls = [r for r in graph['calls'] if graph['nodes'][r['node']]['function']=='B.f' and graph['nodes'][r['node']]['label']=='super().f(x)']
        self.assertTrue(any('::A.f@' in target[1] and '::B@' in target[2] for target in calls[0]['targets']))
        self.assertEqual(len(graph['super_input_inventory']), 1)
        self.assertTrue(self.reachable(graph, self.nodes(graph, kind='Constant', label='7'), self.nodes(graph, kind='return_slot', function='B.f')))

    def test_diamond_super_follows_receiver_mro_past_lexical_start_class(self):
        graph = self.graph({'entry': 'class A:\n def f(self):return 1\nclass B(A):\n def f(self):return super().f()\nclass C(A):\n def f(self):return 2\nclass D(B,C):pass\nD().f()\n'})
        calls = [r for r in graph['calls'] if graph['nodes'][r['node']]['label']=='super().f()']
        self.assertTrue(any('::C.f@' in target[1] and '::D@' in target[2] for target in calls[0]['targets']))
        rows = [r for r in graph['class_dispatch_inventory'] if r['after_class'] and '::D@' in r['receiver_class']]
        self.assertTrue(rows)
        self.assertTrue(all('::B@' not in owner[1] and '::D@' not in owner[1] for row in rows for owner in row['candidate_owners']))
        self.assertTrue(all(not r['dispatch_semantics_accepted'] for r in rows))

    def test_inherited_constructor_receives_the_derived_instance_and_inputs(self):
        graph = self.graph({'entry': 'class A:\n def __init__(self,x):self.x=x\nclass B(A):\n def read(self):return self.x\nB(23).read()\n'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, kind='Constant', label='23'), self.nodes(graph, kind='return_slot', function='B.read')))
        bindings = [e for e in graph['edges'] if e['kind']=='argument' and graph['nodes'][e['target']]['function']=='A.__init__']
        self.assertTrue(bindings)

    def test_ambiguous_declared_bases_keep_all_possible_inherited_bodies(self):
        graph = self.graph({'entry': 'class A:\n def f(self):return 1\nclass B:\n def f(self):return 2\nBase=A\nBase=B\nclass C(Base):pass\nC().f()\n'})
        targets = next(r['targets'] for r in graph['calls'] if graph['nodes'][r['node']]['label']=='C().f()')
        self.assertTrue(any('::A.f@' in target[1] for target in targets))
        self.assertTrue(any('::B.f@' in target[1] for target in targets))
        self.assertIn('class_mro_unresolved', {r['reason'] for r in graph['unclassified']})

    def test_explicit_super_and_shadowed_super_keep_distinct_callable_identities(self):
        graph = self.graph({'entry': 'class A:\n def f(self):return 1\nclass B(A):\n def f(self):return super(B,self).f()\ndef super(a,b):return a\n'})
        self.assertEqual(graph['super_input_inventory'], [])
        self.assertTrue(any('::super@' in t[1] for r in graph['calls'] for t in r['targets']))
        graph = self.graph({'entry': 'class A:\n def f(self):return 1\nclass B(A):\n def f(self):return super(B,self).f()\nB().f()\n'})
        self.assertTrue(any('::A.f@' in t[1] for r in graph['calls'] for t in r['targets']))
        self.assertFalse(graph['super_input_inventory'][0]['implicit'])

    def constructor_storage_fixture(self, body=''):
        source = ('TABLE={"A":{"owner":"A"}}\n'
                  'def make(): return {"owner":TABLE["A"]["owner"]}\n'
                  'def borrow(): return TABLE["A"]\n'
                  'def check(value): return value != make()\ncheck({})\n' + body)
        graph = self.graph({'entry': source})
        row = next(r for r in graph['constructor_global_storage_inventory'] if r['name'] == 'TABLE')
        return graph, row

    def reflective_storage_fixture(self, body):
        graph = self.graph({'dep': 'TABLE={"A":{"owner":"A"}}\n'
            'def make(): return {"owner":TABLE["A"]["owner"]}\n'
            'def check(value): return value != make()\n', 'entry': 'import dep\n' + body})
        return graph, next(r for r in graph['constructor_global_storage_inventory'] if r['name'] == 'TABLE')

    def callable_binding_fixture(self, body=''):
        graph = self.graph({'dep': 'VALUE="A"\n'
            'def leaf(): return {"owner":VALUE}\n'
            'def make(): return leaf()\n'
            'def check(value): return value != make()\n',
            'entry': 'import dep\ndep.check({})\n' + body})
        return graph, next(row for row in graph['constructor_callable_binding_inventory']
                           if row['path'] == 'proof_kernel/dep.py' and row['name'] == 'make')

    def test_constructor_callable_inventory_includes_nested_constructor_calls(self):
        graph, row = self.callable_binding_fixture()
        self.assertEqual({r['name'] for r in graph['constructor_callable_binding_inventory']}, {'make', 'leaf'})
        self.assertEqual(row['contract'], 'python_constructor_callable_binding.v1')
        self.assertEqual(row['status'], 'no_modeled_callable_write_or_escape')
        self.assertEqual(len(row['binding_inputs']), 1)
        self.assertEqual(len(row['declarations']), 1)
        self.assertTrue(row['invocations'])
        self.assertEqual(row['argument_uses'], [])
        for key in ['binding_stability_accepted', 'callable_body_stability_accepted',
                    'function_capture_semantics_accepted', 'native_callback_effects_accepted', 'source_audit_complete']:
            self.assertFalse(row[key])

    def test_constructor_callable_inventory_keeps_original_declaration_after_rebinding(self):
        for body in ['dep.make=dep.leaf\n', 'setattr(dep,"make",dep.leaf)\n', 'delattr(dep,"make")\n']:
            with self.subTest(body=body):
                graph, row = self.callable_binding_fixture(body)
                self.assertEqual(row['status'], 'multiple_binding_inputs')
                self.assertTrue(any(r['kind'] == 'module_attribute_write' for r in row['binding_inputs']))
                self.assertIn('::make@', row['declarations'][0]['identity'])
                self.assertFalse(row['binding_stability_accepted'])

    def test_constructor_callable_inventory_detects_attribute_write_through_alias(self):
        graph, row = self.callable_binding_fixture('chosen=dep.make\nchosen.marker="changed"\n')
        self.assertEqual(row['status'], 'modeled_callable_attribute_write')
        self.assertTrue(any(r['attribute'] == 'marker' and r['write'] for r in row['attribute_uses']))
        self.assertFalse(row['callable_body_stability_accepted'])

    def test_constructor_callable_inventory_distinguishes_invocation_from_opaque_argument(self):
        graph, row = self.callable_binding_fixture('import opaque\nchosen=dep.make\nchosen()\nopaque.take(callback=chosen)\n')
        self.assertEqual(row['status'], 'opaque_callable_escape')
        use = next(r for r in row['argument_uses'] if r['category'] == 'opaque_callable_escape')
        self.assertEqual(use['arguments'][0]['keyword'], 'callback')
        self.assertEqual(use['arguments'][0]['access'], 'direct')
        self.assertEqual(graph['nodes'][use['node']]['label'], 'opaque.take(callback=chosen)')
        self.assertTrue(any(graph['nodes'][r['node']]['label'] == 'chosen()' for r in row['invocations']))

    def test_constructor_callable_inventory_follows_local_returns_and_cyclic_containers(self):
        graph, row = self.callable_binding_fixture('import opaque\n'
            'def relay(value): return {"callback":value}\n'
            'box=[relay(dep.make)]\nbox.append(box)\nopaque.take(box)\n')
        self.assertEqual(row['status'], 'opaque_callable_escape')
        self.assertTrue(any(r['category'] == 'local_call' for r in row['argument_uses']))
        escaped = next(r for r in row['argument_uses'] if graph['nodes'][r['node']]['label'] == 'opaque.take(box)')
        self.assertEqual(escaped['arguments'][0]['access'], 'contained')
        self.assertTrue(any('::relay@' in r['function'] and r['access'] == 'contained' for r in row['return_sites']))

    def test_constructor_callable_inventory_follows_instance_fields_without_unrelated_taint(self):
        graph, row = self.callable_binding_fixture('import opaque\n'
            'class Box:\n def __init__(self, value): self.callback=value\n'
            'def other(): return None\n'
            'opaque.take(Box(dep.make))\nopaque.take(other)\n')
        escaped = [graph['nodes'][r['node']]['label'] for r in row['argument_uses']
                   if r['category'] == 'opaque_callable_escape']
        self.assertIn('opaque.take(Box(dep.make))', escaped)
        self.assertNotIn('opaque.take(other)', escaped)
        self.assertFalse(row['function_capture_semantics_accepted'])

    def test_constructor_callable_containment_cannot_expand_the_exported_module_scope(self):
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        builder = verifier.PythonInputFlowGraph({'proof_kernel/entry.py': b'def make(): return {}\n'})
        with self.assertRaisesRegex(ValueError, '^lcer.containment_record_scope_mismatch$'):
            builder._contained_objects({}, {}, record=True, terminal_functions={'entry::make@1:0'})

    def function_capture_fixture(self, source, dep='def make(): return {}\n'):
        graph = self.graph({'entry': source, 'dep': dep})
        inventory = graph['function_environment_inventory']
        self.assertEqual(inventory['contract'], 'python_function_environment_capture.v1')
        for name in ('namespace_capability_is_module_alias', 'implicit_class_cell_semantics_accepted',
                     'class_object_capture_semantics_accepted', 'annotation_runtime_semantics_accepted',
                     'function_environment_semantics_accepted', 'native_recipient_effects_accepted',
                     'source_audit_complete'):
            self.assertIs(inventory[name], False)
        return graph, inventory

    def test_function_capture_globals_dictionary_is_not_a_module_alias(self):
        graph, inventory = self.function_capture_fixture(
            'from dep import make\nimport opaque\nopaque.take(make)\n')
        use = next(r for r in inventory['opaque_arguments'] if r['targets'] == [['external', 'opaque.take', '']])
        self.assertEqual(use['function_namespaces'], ['dep'])
        self.assertEqual(use['module_objects'], [])
        old = graph['object_containment_inventory']
        self.assertEqual(next(r['modules'] for r in old['root_modules'] if r['node'] == use['node']), [])

    def test_function_capture_globals_retain_imported_module_objects(self):
        _, inventory = self.function_capture_fixture(
            'import dep\nimport opaque\ndef callback(): return 0\nopaque.take(callback)\n')
        use = next(r for r in inventory['opaque_arguments'] if r['targets'] == [['external', 'opaque.take', '']])
        self.assertIn('dep', use['module_objects'])
        self.assertIn('entry', use['function_namespaces'])

    def test_function_capture_defaults_are_values_not_lexical_cells(self):
        _, inventory = self.function_capture_fixture(
            'import opaque\ndef factory():\n import dep\n'
            ' def callback(held=dep.make): return 0\n return callback\nopaque.take(factory())\n')
        callback = next(r for r in inventory['functions'] if r['scope'][1] == 'factory.callback')
        self.assertEqual([r['parameter'] for r in callback['defaults']], ['held'])
        self.assertEqual(callback['closure_cells'], [])
        self.assertEqual(callback['capture_nodes'], [callback['defaults'][0]['node']])
        use = next(r for r in inventory['opaque_arguments'] if r['targets'] == [['external', 'opaque.take', '']])
        self.assertIn('dep', use['function_namespaces'])

    def test_function_capture_propagates_cells_through_intermediate_functions(self):
        _, inventory = self.function_capture_fixture(
            'import opaque\ndef factory():\n import dep\n value=dep\n'
            ' def middle():\n  def leaf(): return value\n  return leaf\n'
            ' return middle\nopaque.take(factory())\n')
        for name in ('factory.middle', 'factory.middle.leaf'):
            row = next(r for r in inventory['functions'] if r['scope'][1] == name)
            self.assertEqual([r['name'] for r in row['closure_cells']], ['value'])
            self.assertEqual(row['closure_cells'][0]['owner_scope'][1], 'factory')
        use = next(r for r in inventory['opaque_arguments'] if r['targets'] == [['external', 'opaque.take', '']])
        self.assertIn('dep', use['module_objects'])

    def test_function_capture_nonlocal_writes_and_unused_declarations_retain_cells(self):
        for body in ('nonlocal value\n  value=1', 'nonlocal value\n  return None'):
            with self.subTest(body=body):
                _, inventory = self.function_capture_fixture(
                    'import opaque\ndef factory():\n import dep\n value=dep\n'
                    ' def callback():\n  '+body+'\n return callback\nopaque.take(factory())\n')
                callback = next(r for r in inventory['functions'] if r['scope'][1] == 'factory.callback')
                self.assertEqual([r['name'] for r in callback['closure_cells']], ['value'])
                use = next(r for r in inventory['opaque_arguments'] if r['targets'] == [['external', 'opaque.take', '']])
                self.assertIn('dep', use['module_objects'])

    def test_function_capture_shadowed_cell_keeps_its_lexical_owner(self):
        _, inventory = self.function_capture_fixture(
            'def factory(value):\n def middle(value):\n  def leaf(): return value\n  return leaf\n return middle\n')
        leaf = next(r for r in inventory['functions'] if r['scope'][1] == 'factory.middle.leaf')
        self.assertEqual(leaf['closure_cells'][0]['owner_scope'][1], 'factory.middle')
        middle = next(r for r in inventory['functions'] if r['scope'][1] == 'factory.middle')
        self.assertEqual(middle['closure_cells'], [])

    def test_function_capture_ignores_unreferenced_factory_locals(self):
        _, inventory = self.function_capture_fixture(
            'import opaque\ndef factory():\n import dep\n unused=dep\n'
            ' def callback(): return 0\n return callback\nopaque.take(factory())\n')
        callback = next(r for r in inventory['functions'] if r['scope'][1] == 'factory.callback')
        self.assertEqual(callback['capture_nodes'], [])
        use = next(r for r in inventory['opaque_arguments'] if r['targets'] == [['external', 'opaque.take', '']])
        self.assertNotIn('dep', use['module_objects'])
        self.assertNotIn('dep', use['function_namespaces'])

    def test_function_capture_follows_cyclic_containers_and_bound_receiver_fields(self):
        _, inventory = self.function_capture_fixture(
            'from dep import make\nimport opaque\nclass Box:\n'
            ' def __init__(self, value): self.value=value\n def callback(self): return 0\n'
            'box=[]\nbox.append(box)\nbox.append(make)\nopaque.take(Box(box).callback)\n')
        use = next(r for r in inventory['opaque_arguments'] if r['targets'] == [['external', 'opaque.take', '']])
        self.assertIn('dep', use['function_namespaces'])
        self.assertIn('entry', use['function_namespaces'])

    def test_function_capture_annotation_values_keep_runtime_semantics_unaccepted(self):
        _, inventory = self.function_capture_fixture(
            'def factory():\n import dep\n def callback(value: dep): return 0\n return callback\n')
        row = next(r for r in inventory['functions'] if r['scope'][1] == 'factory.callback')
        self.assertEqual(row['annotations'][0]['mode'], 'runtime_evaluation_required')
        self.assertTrue(row['annotations'][0]['value_nodes'])
        self.assertTrue(set(row['annotations'][0]['value_nodes']).issubset(row['capture_nodes']))
        self.assertFalse(inventory['annotation_runtime_semantics_accepted'])

    def test_function_capture_cannot_silently_expand_the_old_containment_contract(self):
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        builder = verifier.PythonInputFlowGraph({'proof_kernel/entry.py': b'def make(): return {}\n'})
        with self.assertRaisesRegex(ValueError, '^lcer.containment_record_scope_mismatch$'):
            builder._contained_objects({}, {}, record=True, function_environments={})

    def test_reflective_getter_alias_exposes_helper_borrow_mutation(self):
        graph, row = self.reflective_storage_fixture(
            'lookup=getattr\ndef borrow(module): return lookup(module,"TABLE")\n'
            'table=borrow(dep)\ntable["A"]["owner"]="B"\ndep.check({})\n')
        self.assertTrue(row['mutation_sources'])
        self.assertTrue(any(r['write'] for r in row['subscript_uses']))
        reflection = graph['reflective_attribute_inventory'][0]
        self.assertEqual(reflection['builtin'], 'builtins.getattr')
        self.assertEqual(reflection['selector_literal'], 'TABLE')
        self.assertEqual(reflection['status'], 'literal_attribute_connected')
        self.assertFalse(reflection['effects_accepted'])
        self.assertFalse(graph['source_audit_complete'])

    def test_reflective_setter_and_deletion_invalidate_module_binding(self):
        for body, operation in [('put=setattr\nput(dep,"TABLE",{"A":{"owner":"B"}})\n', 'setattr'),
                                ('remove=delattr\nremove(dep,"TABLE")\n', 'delattr')]:
            with self.subTest(operation=operation):
                graph, row = self.reflective_storage_fixture(body+'dep.check({})\n')
                self.assertEqual(row['status'], 'multiple_binding_inputs')
                self.assertTrue(any(r['kind']=='module_attribute_write' for r in row['binding_inputs']))
                call = graph['reflective_attribute_inventory'][0]
                self.assertEqual(call['operation'], operation)
                self.assertFalse(row['binding_stability_accepted'])
                if operation == 'delattr':
                    self.assertIn(['deleted_binding','TABLE',''], row['binding_references'])

    def test_reflective_getter_retains_callable_and_default_aliases(self):
        graph = self.graph({'dep':'def choose(value): return value\n',
            'entry':'import dep\ndef fallback(value): return "fallback"\n'
                    'lookup=getattr\nselected=lookup(dep,"choose",fallback)\nselected("input")\n'})
        call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph,'Call','selected(\'input\')'))
        names = {target[1].split('::')[1].split('@')[0] for target in call['targets'] if target[0]=='function'}
        self.assertEqual(names, {'choose','fallback'})
        self.assertTrue(any(e['kind']=='reflective_attribute_default' and e['reference'] for e in graph['edges']))

    def test_reflective_hasattr_keeps_read_effect_without_member_alias(self):
        graph, _ = self.reflective_storage_fixture('present=hasattr(dep,"TABLE")\npresent["A"]["owner"]="B"\ndep.check({})\n')
        row = graph['reflective_attribute_inventory'][0]
        links = [e for e in graph['edges'] if e['kind']=='reflective_attribute_result' and e['target']==row['node']]
        self.assertTrue(links)
        self.assertTrue(all(e['reference'] is False for e in links))
        self.assertFalse(graph['constructor_global_storage_inventory'][0]['mutation_sources'])

    def test_reflective_dynamic_selector_and_expansion_stay_unresolved(self):
        for source, status in [('def use(module,name): return getattr(module,name)\n', 'selector_unresolved'),
                               ('def use(module,args): return getattr(module,*args)\n', 'argument_shape_unresolved')]:
            with self.subTest(source=source):
                graph = self.graph({'entry':source})
                row = graph['reflective_attribute_inventory'][0]
                self.assertEqual(row['status'], status)
                self.assertIsNone(row['attribute_node'])
                self.assertFalse(row['effects_accepted'])

    def test_reflective_alias_rejects_forbidden_introspection_with_exact_edge(self):
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        for name in ['__globals__','__dict__','__code__','__import__']:
            with self.subTest(name=name), self.assertRaises(verifier.SourceInputForbidden) as caught:
                self.graph({'entry':'lookup=getattr\ndef read(value): return lookup(value,%r)\n' % name})
            self.assertEqual(str(caught.exception),'lcer.source_input_forbidden')
            self.assertEqual(caught.exception.edge, {'path':'proof_kernel/entry.py','function':'read',
                'input':'platform','callee':'getattr.'+name,'line':2})

    def test_reflective_builtin_spelling_does_not_override_local_callable(self):
        graph = self.graph({'entry':'def getattr(value,name): return value\n'
                           'def use(value): return getattr(value,"TABLE")\n'})
        self.assertEqual(graph['reflective_attribute_inventory'], [])

    def test_constructor_storage_tracks_borrowed_rows_without_claiming_mutation_closure(self):
        graph, row = self.constructor_storage_fixture('row=borrow()\nowner=row["owner"]\n')
        self.assertEqual(row['status'], 'no_modeled_write_or_opaque_borrow_escape')
        self.assertEqual(len(row['objects']), 2)
        self.assertTrue(any('::borrow@' in r['function'] for r in row['local_return_sites']))
        self.assertTrue(row['subscript_uses'])
        self.assertTrue(row['unresolved'])
        self.assertFalse(row['module_initialization_accepted'])
        self.assertFalse(row['storage_mutation_closure_accepted'])
        self.assertFalse(graph['source_audit_complete'])

    def test_constructor_storage_detects_direct_module_namespace_escape(self):
        graph, row = self.constructor_storage_fixture('import entry\nimport opaque\nopaque.take(entry)\n')
        self.assertEqual(row['contract'], 'python_constructor_global_storage.v2')
        self.assertEqual(row['status'], 'opaque_namespace_escape')
        namespace = row['module_namespace']
        self.assertEqual(namespace['contract'], 'python_module_namespace_use.v1')
        escaped = next(r for r in namespace['argument_uses'] if r['category'] == 'opaque_namespace_escape')
        self.assertEqual(escaped['targets'], [['external', 'opaque.take', '']])
        self.assertEqual(escaped['arguments'][0]['access'], 'direct')
        self.assertEqual(graph['nodes'][escaped['node']]['label'], 'opaque.take(entry)')
        self.assertEqual(row['call_uses'], [])
        self.assertFalse(namespace['namespace_effects_accepted'])
        self.assertFalse(row['storage_mutation_closure_accepted'])

    def test_constructor_module_escape_tracks_returned_aliases_and_keywords(self):
        _, row = self.constructor_storage_fixture('import entry\nimport opaque\n'
            'def relay(value): return value\nchosen=relay(entry)\nopaque.take(module=chosen)\n')
        namespace = row['module_namespace']
        self.assertEqual(row['status'], 'opaque_namespace_escape')
        self.assertTrue(any('::relay@' in r['function'] for r in namespace['return_sites']))
        self.assertTrue(any(r['category'] == 'local_call' for r in namespace['argument_uses']))
        escaped = next(r for r in namespace['argument_uses'] if r['category'] == 'opaque_namespace_escape')
        self.assertEqual(escaped['arguments'][0]['keyword'], 'module')
        self.assertEqual(escaped['arguments'][0]['access'], 'direct')

    def test_constructor_module_escape_follows_cyclic_container_storage(self):
        _, row = self.constructor_storage_fixture('import entry\nimport opaque\n'
            'box=[]\nbox.append(box)\nbox.append(entry)\nopaque.take(box)\n')
        escaped = next(r for r in row['module_namespace']['argument_uses']
                       if r['targets'] == [['external', 'opaque.take', '']])
        self.assertEqual(row['status'], 'opaque_namespace_escape')
        self.assertEqual(escaped['arguments'][0]['access'], 'contained')
        self.assertFalse(row['module_namespace']['namespace_effects_accepted'])

    def test_constructor_module_escape_follows_instance_fields(self):
        _, row = self.constructor_storage_fixture('import entry\nimport opaque\n'
            'class Box:\n def __init__(self, value): self.value=value\n'
            'opaque.take(Box(entry))\n')
        escaped = next(r for r in row['module_namespace']['argument_uses']
                       if r['targets'] == [['external', 'opaque.take', '']])
        self.assertEqual(row['status'], 'opaque_namespace_escape')
        self.assertEqual(escaped['arguments'][0]['access'], 'contained')

    def test_constructor_namespace_local_read_is_not_an_opaque_call(self):
        graph, row = self.constructor_storage_fixture('import entry\n'
            'def read(module): return module.TABLE["A"]["owner"]\nread(entry)\n')
        namespace = row['module_namespace']
        self.assertEqual(row['status'], 'no_modeled_write_or_opaque_borrow_escape')
        self.assertEqual(namespace['status'], 'no_modeled_namespace_escape')
        self.assertTrue(namespace['argument_uses'])
        self.assertTrue(all(r['category'] == 'local_call' for r in namespace['argument_uses']))
        self.assertTrue(any(r['attribute'] == 'TABLE' and not r['write'] for r in namespace['attribute_uses']))
        self.assertFalse(namespace['namespace_effects_accepted'])
        self.assertFalse(graph['source_audit_complete'])

    def test_constructor_namespace_escape_does_not_contaminate_unrelated_modules(self):
        graph = self.graph({'dep': 'TABLE={"A":{"owner":"A"}}\n'
                                   'def make(): return {"owner":TABLE["A"]["owner"]}\n'
                                   'def check(value): return value != make()\n',
                            'other': 'VALUE=1\n',
                            'entry': 'import dep\nimport other\nimport opaque\ndep.check({})\nopaque.take(other)\n'})
        row = next(r for r in graph['constructor_global_storage_inventory'] if r['name'] == 'TABLE')
        self.assertEqual(row['module_namespace']['module'], 'dep')
        self.assertEqual(row['module_namespace']['status'], 'no_modeled_namespace_escape')
        self.assertEqual(row['status'], 'no_modeled_write_or_opaque_borrow_escape')
        self.assertEqual(row['module_namespace']['argument_uses'], [])

    def containment_argument(self, graph, call_label):
        inventory = graph['object_containment_inventory']
        call = next(row for row in inventory['argument_roots']
                    if graph['nodes'][row['call_node']]['label'] == call_label)
        root = call['positional'][0]
        nodes = {row['node']: row for row in inventory['nodes']}
        outgoing = {}
        for edge in inventory['storage_edges']:
            outgoing.setdefault(edge['source'], set()).add(edge['target'])
        seen, pending, modules = set(), [root], set()
        while pending:
            number = pending.pop()
            if number in seen:
                continue
            seen.add(number)
            modules.update(row['identity'] for row in nodes[number]['objects'] if row['kind'] == 'module')
            pending.extend(outgoing.get(number, ()))
        reported = next(row['modules'] for row in inventory['root_modules'] if row['node'] == root)
        self.assertEqual(reported, sorted(modules))
        self.assertFalse(inventory['reference_seed_semantics_accepted'])
        self.assertFalse(inventory['receiver_effects_accepted'])
        self.assertFalse(inventory['module_mutation_effects_accepted'])
        self.assertFalse(inventory['source_audit_complete'])
        return inventory, seen, sorted(modules)

    def test_containment_inventory_exposes_direct_module_seeds_deterministically(self):
        sources = {'dep': 'VALUE=1\n', 'entry': 'import dep\nimport opaque\nopaque.take(dep)\n'}
        graph = self.graph(sources)
        inventory, _, modules = self.containment_argument(graph, 'opaque.take(dep)')
        self.assertEqual(inventory['contract'], 'python_object_containment_graph.v2')
        self.assertEqual(modules, ['dep'])
        self.assertTrue(any(row['kind'] == 'module' and row['identity'] == 'dep'
                            for row in inventory['reference_seeds']))
        self.assertEqual(inventory, self.graph(dict(reversed(list(sources.items()))))['object_containment_inventory'])

    def test_containment_inventory_replays_cyclic_container_module_storage(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry':
            'import dep\nimport opaque\nbox=[]\nbox.append(box)\nbox.append(dep)\nopaque.take(box)\n'})
        inventory, visited, modules = self.containment_argument(graph, 'opaque.take(box)')
        self.assertEqual(modules, ['dep'])
        members = {row['members_node'] for row in inventory['containers']}
        self.assertTrue(visited & members)
        self.assertTrue(any(edge['source'] == edge['target'] for edge in inventory['storage_edges']))

    def test_containment_inventory_includes_dictionary_key_module_paths(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry':
            'import dep\nimport opaque\nbox={dep:0}\nopaque.take(box)\n'})
        inventory, visited, modules = self.containment_argument(graph, 'opaque.take(box)')
        self.assertEqual(modules, ['dep'])
        keys = {row['keys_node'] for row in inventory['containers'] if row['keys_node'] is not None}
        self.assertTrue(visited & keys)

    def test_containment_inventory_keeps_unrelated_instance_fields_separate(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry':
            'import dep\nimport opaque\n'
            'class Box:\n def __init__(self): self.payload=dep\n'
            'class Other:\n def __init__(self): self.payload=0\n'
            'box=Box()\nother=Other()\nopaque.take(box)\nopaque.take(other)\n'})
        inventory, visited, modules = self.containment_argument(graph, 'opaque.take(box)')
        self.assertEqual(modules, ['dep'])
        self.assertEqual(self.containment_argument(graph, 'opaque.take(other)')[2], [])
        fields = [row for row in inventory['instance_fields'] if row['attribute'] == 'payload']
        self.assertEqual(len(fields), 2)
        self.assertEqual(len({row['owner'] for row in fields}), 2)
        self.assertEqual(len(visited & {row['node'] for row in fields}), 1)

    def test_containment_inventory_follows_returned_nested_container_aliases(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry':
            'import dep\nimport opaque\n'
            'def pack(value): return {"nested":([value],)}\n'
            'chosen=pack(dep)\nopaque.take(chosen)\n'})
        inventory, visited, modules = self.containment_argument(graph, 'opaque.take(chosen)')
        self.assertEqual(modules, ['dep'])
        kinds = {row['kind'] for row in inventory['containers'] if row['members_node'] in visited}
        self.assertEqual(kinds, {'dict', 'tuple', 'list'})

    def test_containment_inventory_does_not_turn_computed_values_into_module_aliases(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry':
            'import dep\nimport opaque\nvalue=hash(dep)\nopaque.take(value)\n'})
        self.assertEqual(self.containment_argument(graph, 'hash(dep)')[2], ['dep'])
        self.assertEqual(self.containment_argument(graph, 'opaque.take(value)')[2], [])

    def test_bound_callback_retains_module_bearing_receiver_without_invocation(self):
        graph, row = self.constructor_storage_fixture('import entry\nimport opaque\n'
            'class Box:\n def __init__(self): self.payload=entry\n def callback(self): return None\n'
            'box=Box()\nopaque.take(box.callback)\n')
        self.assertEqual(row['status'], 'opaque_namespace_escape')
        inventory, _, modules = self.containment_argument(graph, 'opaque.take(box.callback)')
        self.assertEqual(modules, ['entry'])
        self.assertTrue(any(r['kind'] == 'bound' and '::Box@' in r['receiver']
                            and '::Box.callback@' in r['identity'] for r in inventory['reference_seeds']))
        self.assertFalse(inventory['bound_receiver_binding_semantics_accepted'])
        self.assertFalse(inventory['function_global_capture_semantics_accepted'])

    def test_bound_callback_receiver_survives_helper_return_and_container_storage(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry': 'import dep\nimport opaque\n'
            'class Box:\n def __init__(self): self.payload=dep\n def callback(self): return None\n'
            'def relay(value): return value\nbox=Box()\ncallbacks={"chosen":[relay(box.callback)]}\n'
            'opaque.take(callbacks)\n'})
        self.assertEqual(self.containment_argument(graph, 'opaque.take(callbacks)')[2], ['dep'])

    def test_bound_callback_receiver_storage_closes_cycles(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry': 'import dep\nimport opaque\n'
            'class Box:\n def __init__(self):\n  self.payload=dep\n  self.loop=[self]\n'
            ' def callback(self): return None\nbox=Box()\nopaque.take(box.callback)\n'})
        inventory, visited, modules = self.containment_argument(graph, 'opaque.take(box.callback)')
        self.assertEqual(modules, ['dep'])
        self.assertTrue(any(r['attribute'] == 'loop' and r['node'] in visited for r in inventory['instance_fields']))

    def test_bound_callback_receiver_keeps_other_classes_separate(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry': 'import dep\nimport opaque\n'
            'class Box:\n def __init__(self): self.payload=dep\n def callback(self): return None\n'
            'class Other:\n def __init__(self): self.payload=0\n def callback(self): return None\n'
            'box=Box()\nother=Other()\nopaque.take(box.callback)\nopaque.take(other.callback)\n'})
        self.assertEqual(self.containment_argument(graph, 'opaque.take(box.callback)')[2], ['dep'])
        self.assertEqual(self.containment_argument(graph, 'opaque.take(other.callback)')[2], [])

    def test_callable_without_bound_receiver_does_not_invent_receiver_storage(self):
        for decorator, selection in [('@staticmethod\n ', 'box.callback'), ('', 'Box.callback')]:
            with self.subTest(selection=selection):
                graph = self.graph({'dep': 'VALUE=1\n', 'entry': 'import dep\nimport opaque\n'
                    'class Box:\n def __init__(self): self.payload=dep\n '+decorator+
                    'def callback(): return None\nbox=Box()\nopaque.take('+selection+')\n'})
                inventory, visited, _ = self.containment_argument(graph, 'opaque.take('+selection+')')
                root = next(r['positional'][0] for r in inventory['argument_roots']
                            if graph['nodes'][r['call_node']]['label'] == 'opaque.take('+selection+')')
                value = next(r for r in inventory['nodes'] if r['node'] == root)
                self.assertFalse(any(r['kind'] == 'bound' for r in value['objects']))
                self.assertFalse(inventory['function_global_capture_semantics_accepted'])

    def test_bound_callback_receiver_survives_a_second_holder_instance(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry': 'import dep\nimport opaque\n'
            'class Box:\n def __init__(self): self.payload=dep\n def callback(self): return None\n'
            'class Holder:\n def __init__(self, callback): self.callback=callback\n'
            'box=Box()\nholder=Holder(box.callback)\nopaque.take(holder)\n'})
        self.assertEqual(self.containment_argument(graph, 'opaque.take(holder)')[2], ['dep'])

    def receiver_call(self, graph, label):
        inventory = graph['call_receiver_inventory']
        self.assertEqual(inventory['contract'], 'python_call_receiver_inventory.v1')
        for name in ['descriptor_binding_accepted', 'receiver_effects_accepted',
                     'module_mutation_effects_accepted', 'source_audit_complete']:
            self.assertIs(inventory[name], False)
        call = next(row for row in inventory['calls'] if graph['nodes'][row['call_node']]['label'] == label)
        modules = sorted({module for row in inventory['module_receivers']
                          if row['call_node'] == call['call_node'] and row['callee_node'] == call['callee_node']
                          for module in row['modules']})
        return call, modules

    def test_receiver_inventory_records_direct_attribute_selection_deterministically(self):
        sources = {'dep': 'VALUE=1\n', 'entry': 'import dep\n'
            'class Box:\n def __init__(self): self.payload=dep\nbox=Box()\nbox.external()\n'}
        graph = self.graph(sources)
        call, modules = self.receiver_call(graph, 'box.external()')
        self.assertEqual(call['status'], 'nonlocal_or_unresolved')
        self.assertEqual(modules, ['dep'])
        self.assertEqual(graph['call_receiver_inventory'],
                         self.graph(dict(reversed(list(sources.items()))))['call_receiver_inventory'])

    def test_receiver_inventory_follows_method_alias_through_local_return(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry': 'import dep\n'
            'class Box:\n def __init__(self): self.payload=dep\n'
            'def relay(value): return value\nbox=Box()\nchosen=relay(box.external)\nchosen()\n'})
        call, modules = self.receiver_call(graph, 'chosen()')
        self.assertEqual(modules, ['dep'])
        accesses = graph['call_receiver_inventory']['accesses']
        self.assertTrue(any(accesses[index]['attribute'] == 'external' for index in call['access_origins']))

    def test_receiver_inventory_follows_stored_callable_selection(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry': 'import dep\n'
            'class Box:\n def __init__(self): self.payload=dep\n'
            'box=Box()\ncallbacks=[box.external]\nchosen=callbacks[0]\nchosen()\n'})
        self.assertEqual(self.receiver_call(graph, 'chosen()')[1], ['dep'])

    def test_receiver_inventory_keeps_local_methods_separate_from_opaque_receivers(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry': 'import dep\n'
            'class Box:\n def __init__(self): self.payload=dep\n def local(self): return 1\n'
            'box=Box()\nbox.local()\n'})
        call, modules = self.receiver_call(graph, 'box.local()')
        self.assertEqual(call['status'], 'local_callable')
        self.assertEqual(modules, [])

    def test_receiver_inventory_preserves_class_qualified_storage_isolation(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry': 'import dep\n'
            'class Box:\n def __init__(self): self.payload=dep\n'
            'class Other:\n def __init__(self): self.payload=0\n'
            'box=Box()\nother=Other()\nbox.external()\nother.external()\n'})
        self.assertEqual(self.receiver_call(graph, 'box.external()')[1], ['dep'])
        self.assertEqual(self.receiver_call(graph, 'other.external()')[1], [])

    def test_receiver_inventory_does_not_alias_computed_hash_results(self):
        graph = self.graph({'dep': 'VALUE=1\n', 'entry': 'import dep\n'
            'class Box:\n def __init__(self): self.payload=dep\n'
            'box=Box()\nvalue=hash(box.external)\nvalue()\n'})
        inventory = graph['call_receiver_inventory']
        self.assertFalse(any(graph['nodes'][row['call_node']]['label'] == 'value()'
                             for row in inventory['calls']))

    def test_argument_containment_record_rejects_receiver_scope_expansion(self):
        import verify_live_cross_domain_evidence_round_trip_release as bootstrap
        builder = bootstrap.PythonInputFlowGraph({'proof_kernel/entry.py': b'value=1\n'})
        with self.assertRaisesRegex(ValueError, '^lcer.containment_record_scope_mismatch$'):
            builder._contained_objects({}, {}, record=True, extra_roots={0})

    def test_constructor_storage_finds_direct_and_helper_mediated_borrow_writes(self):
        for body, owner in [('row=borrow()\nrow["owner"]="B"\n', '<module>'),
                            ('def mutate(row): row["owner"]="B"\nmutate(borrow())\n', 'mutate')]:
            with self.subTest(body=body):
                graph, row = self.constructor_storage_fixture(body)
                self.assertEqual(row['status'], 'modeled_storage_write')
                self.assertTrue(any(graph['nodes'][r['node']]['function'] == owner for r in row['mutation_sources']))
                self.assertTrue(any(r['write'] for r in row['subscript_uses']))

    def test_constructor_storage_retains_opaque_borrow_argument_escape(self):
        graph, row = self.constructor_storage_fixture('import opaque\nopaque.take(borrow())\n')
        self.assertEqual(row['status'], 'opaque_borrow_escape')
        call = next(r for r in row['call_uses'] if r['category'] == 'opaque_call')
        self.assertEqual(call['targets'], [['external', 'opaque.take', '']])
        self.assertTrue(call['arguments'][0]['objects'])
        self.assertEqual(graph['nodes'][call['node']]['label'], 'opaque.take(borrow())')

    def test_constructor_storage_detects_mutating_container_methods(self):
        graph, row = self.constructor_storage_fixture('row=borrow()\nrow.clear()\n')
        self.assertEqual(row['status'], 'modeled_storage_write')
        self.assertTrue(any(graph['nodes'][r['node']]['label'] == 'row.clear()' for r in row['mutation_sources']))
        self.assertTrue(any(r['category'] == 'container_call' and r['receiver_objects'] for r in row['call_uses']))

    def test_constructor_storage_binds_local_module_replacement_to_its_namespace(self):
        graph = self.graph({'dep': 'TABLE={"A":{"owner":"A"}}\n'
                                   'def make(): return {"owner":TABLE["A"]["owner"]}\n'
                                   'def check(value): return value != make()\n',
                            'entry': 'import dep\ndep.TABLE={"A":{"owner":"B"}}\ndep.check({})\n'})
        row = next(r for r in graph['constructor_global_storage_inventory'] if r['name'] == 'TABLE')
        self.assertEqual(row['status'], 'multiple_binding_inputs')
        self.assertTrue(any(r['kind'] == 'module_attribute_write' for r in row['binding_inputs']))
        self.assertEqual(len(row['root_objects']), 2)
        self.assertFalse(row['binding_stability_accepted'])

    def test_constructor_storage_does_not_attribute_fresh_copy_writes_to_the_borrowed_row(self):
        _, row = self.constructor_storage_fixture('copied=borrow().copy()\ncopied["owner"]="B"\n')
        self.assertEqual(row['status'], 'no_modeled_write_or_opaque_borrow_escape')
        self.assertEqual(row['mutation_sources'], [])
        self.assertFalse(any(r['write'] for r in row['subscript_uses']))
        self.assertFalse(row['storage_mutation_closure_accepted'])

    def test_local_module_member_write_preserves_original_and_replacement_call_targets(self):
        graph = self.graph({'dep': 'def choose(value): return "original"\n',
                            'entry': 'import dep\ndef replacement(value): return value\n'
                                     'dep.choose=replacement\ndef read(value): return dep.choose(value)\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'dep.choose(value)'))
        self.assertEqual(call['targets'], [['function', 'proof_kernel/dep.py::choose@1:0', ''],
                                           ['function', 'proof_kernel/entry.py::replacement@2:0', '']])
        self.assertTrue(any(row['reason'] == 'module_attribute_write_summary_required:choose'
                            for row in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])

    def test_local_module_alias_write_reaches_from_import_and_module_global_call(self):
        graph = self.graph({'dep': 'def choose(value): return "original"\n'
                                   'def forward(value): return choose(value)\n',
                            'entry': 'import dep\nfrom dep import choose as selected\nalias=dep\n'
                                     'def replacement(value): return value\nalias.choose=replacement\n'
                                     'def read(value): return selected(value), dep.forward(value)\n'})
        for label in ('selected(value)', 'choose(value)'):
            with self.subTest(call=label):
                call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
                self.assertIn(['function', 'proof_kernel/entry.py::replacement@4:0', ''], call['targets'])
        self.assertFalse(graph['source_audit_complete'])

    def test_local_module_member_write_does_not_alias_another_module_or_member(self):
        for assignment in ('other.choose=replacement', 'dep.unrelated=replacement'):
            with self.subTest(assignment=assignment):
                graph = self.graph({'dep': 'def choose(value): return "original"\n',
                                    'other': 'def choose(value): return "other"\n',
                                    'entry': 'import dep, other\ndef replacement(value): return value\n'
                                             + assignment + '\ndef read(value): return dep.choose(value)\n'})
                call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'dep.choose(value)'))
                self.assertEqual(call['targets'], [['function', 'proof_kernel/dep.py::choose@1:0', '']])

    def test_new_local_module_member_carries_external_input_to_consequence(self):
        graph = self.graph({'dep': 'VALUE=0\n',
                            'entry': 'import dep, os\ndep.read=os.getenv\nowner=dep.read("OWNER")\n'})
        call_nodes = self.nodes(graph, 'Call', "dep.read('OWNER')")
        call = next(row for row in graph['calls'] if row['node'] in call_nodes)
        self.assertEqual(call['targets'], [['external', 'os.getenv', '']])
        self.assertTrue(self.reachable(graph, call_nodes, self.nodes(graph, 'symbol', 'owner', '<module>')))
        self.assertTrue(any(row['reason'] == 'module_attribute_write_summary_required:read'
                            for row in graph['unclassified']))

    def test_local_module_parameter_alias_write_reaches_later_module_read(self):
        graph = self.graph({'dep': 'def choose(value): return "original"\n',
                            'entry': 'import dep\ndef replacement(value): return value\n'
                                     'def install(target): target.choose=replacement\ninstall(dep)\n'
                                     'def read(value): return dep.choose(value)\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'dep.choose(value)'))
        self.assertIn(['function', 'proof_kernel/entry.py::replacement@2:0', ''], call['targets'])
        self.assertFalse(graph['source_audit_complete'])

    def test_context_target_receives_enter_result_without_manager_alias(self):
        graph = self.graph({'entry': 'import os\nclass C:\n    def __enter__(self):\n        return os.getpid\n'
                            '    def __exit__(self, kind, value, trace):\n        return False\nwith C() as fn:\n    fn()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
        self.assertEqual(call['targets'], [['external', 'os.getpid', '']])
        self.assertEqual({row['method'] for row in graph['builtin_protocol_edges']}, {'__enter__', '__exit__'})
        self.assertFalse(any(edge['kind'] == 'context_receiver' and edge['reference'] for edge in graph['edges']))

    def test_context_enter_pid_reaches_bound_value_and_body_control(self):
        graph = self.graph({'entry': 'import os\nclass C:\n    def __enter__(self):\n        return os.getpid() % 2\n'
                            '    def __exit__(self, kind, value, trace):\n        return False\n'
                            'with C() as owner:\n    chosen = owner\n    activated = True\n'})
        for label in ('owner', 'chosen', 'activated'):
            self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                           self.nodes(graph, 'symbol', label, '<module>')))

    def test_context_exit_suppression_reaches_following_statements(self):
        for body in ('raise ValueError()', 'work()'):
            with self.subTest(body=body):
                graph = self.graph({'entry': 'import os\nclass C:\n    def __enter__(self):\n        return None\n'
                                    '    def __exit__(self, kind, value, trace):\n        return os.getpid() % 2\n'
                                    'with C():\n    ' + body + '\nowner = "A"\n'})
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                               self.nodes(graph, 'symbol', 'owner', '<module>')))
                self.assertTrue(any(row['reason'] == 'context_exception_suppression_summary_required'
                                    for row in graph['unclassified']))

    def test_context_exit_truth_dispatches_bool_or_len_without_closing_effects(self):
        for method in ('__bool__', '__len__'):
            with self.subTest(method=method):
                graph = self.graph({'entry': 'import os\nclass Truth:\n    def ' + method + '(self):\n'
                                    '        return os.getpid() % 2\nclass C:\n    def __enter__(self):\n        return None\n'
                                    '    def __exit__(self, kind, value, trace):\n        return Truth()\n'
                                    'with C():\n    raise ValueError()\nowner = "A"\n'})
                self.assertTrue(any(row['builtin'] == 'context_exit_truth' and row['method'] == method
                                    for row in graph['builtin_protocol_edges']))
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                               self.nodes(graph, 'symbol', 'owner', '<module>')))
                self.assertFalse(graph['source_audit_complete'])

    def test_context_exit_invalid_bool_does_not_fall_back_to_len(self):
        graph = self.graph({'entry': 'class Truth:\n    __bool__ = None\n    def __len__(self):\n        return 1\n'
                            'class C:\n    def __enter__(self):\n        return None\n'
                            '    def __exit__(self, kind, value, trace):\n        return Truth()\n'
                            'with C():\n    raise ValueError()\n'})
        self.assertFalse(any(row['builtin'] == 'context_exit_truth' and row['method'] == '__len__'
                             for row in graph['builtin_protocol_edges']))
        self.assertTrue(any(row['reason'] == 'special_method_binding_summary_required:context_exit_truth.__bool__'
                            for row in graph['unclassified']))

    def test_context_exit_binds_three_exception_inputs_with_body_provenance(self):
        graph = self.graph({'entry': 'import os\nclass C:\n    def __enter__(self):\n        return None\n'
                            '    def __exit__(self, kind, value, trace):\n        return value\n'
                            'with C():\n    raise ValueError(os.getpid())\n'})
        context = graph['context_inventory'][0]
        callback = next(row for row in graph['builtin_protocol_edges'] if row['method'] == '__exit__')
        self.assertEqual(callback['argument_nodes'], context['exception_nodes'])
        for source, name in zip(context['exception_nodes'], ('kind', 'value', 'trace')):
            parameters = self.nodes(graph, 'symbol', name, 'C.__exit__')
            self.assertTrue(any(edge['source'] == source and edge['target'] in parameters
                                and edge['kind'] == 'argument' and edge['reference'] for edge in graph['edges']))
            self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), {source}))
        self.assertTrue(any(row['reason'] == 'context_exception_state_summary_required' for row in graph['unclassified']))

    def test_context_exit_result_never_becomes_the_as_target_callable(self):
        graph = self.graph({'entry': 'import os, time\nclass C:\n    def __enter__(self):\n        return os.getpid\n'
                            '    def __exit__(self, kind, value, trace):\n        return time.monotonic\n'
                            'with C() as fn:\n    fn()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
        self.assertEqual(call['targets'], [['external', 'os.getpid', '']])
        self.assertFalse(any(target[1] == 'time.monotonic' for row in graph['calls'] for target in row['targets']))

    def test_context_type_slots_bypass_instance_shadowing(self):
        graph = self.graph({'entry': 'import os, time\nclass C:\n    def __enter__(self):\n        return os.getpid\n'
                            '    def __exit__(self, kind, value, trace):\n        return False\n'
                            'c=C()\nc.__enter__ = time.monotonic\nwith c as fn:\n    fn()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
        self.assertEqual(call['targets'], [['external', 'os.getpid', '']])

    def test_nested_context_unwinding_reaches_outer_exit_and_enclosing_continuation(self):
        graph = self.graph({'entry': 'import os\nclass C:\n    def __enter__(self):\n        return None\n'
                            '    def __exit__(self, kind, value, trace):\n        return os.getpid() % 2\n'
                            'if flag:\n    with C(), C():\n        work()\nowner = "A"\n'})
        contexts = graph['context_inventory']
        self.assertEqual(len(contexts), 2)
        self.assertEqual(contexts[1]['inner_exit_node'], contexts[0]['suppression_node'])
        self.assertTrue(any(edge['source'] == contexts[0]['suppression_node'] and edge['target'] == contexts[1]['exit_node']
                            and edge['kind'] == 'context_unwind_control' and not edge['reference'] for edge in graph['edges']))
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                       self.nodes(graph, 'symbol', 'owner', '<module>')))

    def test_context_enter_tuple_result_preserves_unpack_callable_elements(self):
        graph = self.graph({'entry': 'import os, time\nclass C:\n    def __enter__(self):\n'
                            '        return (os.getpid, time.monotonic)\n'
                            '    def __exit__(self, kind, value, trace):\n        return False\n'
                            'with C() as (first, second):\n    first()\n    second()\n'})
        for label, target in [('first()', 'os.getpid'), ('second()', 'time.monotonic')]:
            call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
            self.assertEqual(call['targets'], [['external', target, '']])

    def test_async_context_does_not_treat_awaitable_as_entered_value(self):
        graph = self.graph({'entry': 'import os\nclass C:\n    async def __aenter__(self):\n        return os.getpid\n'
                            '    async def __aexit__(self, kind, value, trace):\n        return False\n'
                            'async def f():\n    async with C() as fn:\n        fn()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
        self.assertEqual(call['targets'], [])
        self.assertTrue(any(row['reason'] == 'async_context_manager_summary_required' for row in graph['unclassified']))
        self.assertEqual({row['method'] for row in graph['builtin_protocol_edges']}, {'__aenter__', '__aexit__'})

    def test_unknown_context_and_custom_descriptor_remain_open(self):
        for source in ('with unknown as fn:\n    fn()\n',
                       'class C:\n    @property\n    def __enter__(self):\n        return target\n'
                       '    def __exit__(self, kind, value, trace):\n        return False\nwith C() as fn:\n    fn()\n'):
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                self.assertTrue(any(row['reason'] == 'context_manager_summary_required' for row in graph['unclassified']))
                self.assertTrue(all(not row['effects_complete'] for row in graph['context_inventory']))
                self.assertFalse(graph['source_audit_complete'])

    def test_star_call_binds_items_without_copying_bound_receiver(self):
        graph = self.graph({'entry': 'import os\nclass C:\n    def f(self, fn):\n        fn()\n'
                            'c = C()\nc.f(*[os.getpid])\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
        self.assertEqual(call['targets'], [['external', 'os.getpid', '']])
        receivers = self.nodes(graph, 'bound_receiver')
        fn = self.nodes(graph, 'symbol', 'fn', 'C.f')
        self.assertFalse(any(edge['source'] in receivers and edge['target'] in fn
                             and edge['reference'] for edge in graph['edges']))
        self.assertTrue(any(row['reason'] == 'expanded_argument_binding_summary_required' for row in graph['unclassified']))

    def test_star_call_traces_callable_emitted_by_custom_iterator(self):
        graph = self.graph({'entry': 'import os\nclass I:\n    def __iter__(self):\n        return self\n'
                            '    def __next__(self):\n        return os.getpid\n'
                            'def f(fn):\n    fn()\nf(*I())\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
        self.assertEqual(call['targets'], [['external', 'os.getpid', '']])
        self.assertTrue(any(row['method'] == '__next__' for row in graph['builtin_protocol_edges']))
        self.assertFalse(graph['source_audit_complete'])

    def test_expansion_cannot_overwrite_fixed_positional_prefix(self):
        for expansion in ('*[os.getpid]', "**{'second': os.getpid}"):
            with self.subTest(expansion=expansion):
                graph = self.graph({'entry': 'import os, time\ndef f(first, second):\n'
                                    '    first()\n    second()\nf(time.monotonic, ' + expansion + ')\n'})
                for label, target in [('first()', 'time.monotonic'), ('second()', 'os.getpid')]:
                    call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
                    self.assertEqual(call['targets'], [['external', target, '']])

    def test_variadic_formals_are_containers_not_argument_callable_aliases(self):
        for signature, actual, selected in [('*args', 'os.getpid', 'args[0]'),
                                             ('**kwargs', 'fn=os.getpid', "kwargs['fn']")]:
            with self.subTest(signature=signature):
                name = signature.lstrip('*')
                graph = self.graph({'entry': 'import os\ndef f(' + signature + '):\n    ' + name + '()\n    '
                                    + selected + '()\nf(' + actual + ')\n'})
                packed = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', name + '()'))
                self.assertTrue(packed['targets'])
                self.assertEqual({target[0] for target in packed['targets']}, {'container'})
                item = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', selected + '()'))
                self.assertEqual(item['targets'], [['external', 'os.getpid', '']])
                self.assertTrue(any(row['node'] == packed['node'] and row['reason'] == 'callable_identity_unclassified:container'
                                    for row in graph['unclassified']))

    def test_bound_method_with_only_varargs_packs_receiver_at_zero(self):
        graph = self.graph({'entry': 'import os\nclass C:\n    def f(*args):\n        args[0]()\n'
                            '        args[1]()\nc = C()\nc.f(os.getpid)\n'})
        first = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'args[0]()'))
        second = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'args[1]()'))
        self.assertEqual({target[0] for target in first['targets']}, {'instance'})
        self.assertEqual(second['targets'], [['external', 'os.getpid', '']])

    def test_keyword_expansion_traces_mapping_values_and_custom_lookup(self):
        for mapping in ("{'fn': os.getpid}", 'M()'):
            with self.subTest(mapping=mapping):
                graph = self.graph({'entry': 'import os\nclass M:\n    def keys(self):\n        return ["fn"]\n'
                                    '    def __getitem__(self, key):\n        return os.getpid\n'
                                    'def f(fn):\n    fn()\nf(**' + mapping + ')\n'})
                call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
                self.assertEqual(call['targets'], [['external', 'os.getpid', '']])
                self.assertTrue(any(row['reason'] == 'keyword_expansion_protocol_summary_required'
                                    for row in graph['unclassified']))

    def test_positional_only_keyword_name_goes_to_kwargs(self):
        graph = self.graph({'entry': 'import os, time\ndef f(fn, /, **kwargs):\n    fn()\n'
                            '    kwargs["fn"]()\nf(time.monotonic, fn=os.getpid)\n'})
        for label, target in [('fn()', 'time.monotonic'), ("kwargs['fn']()", 'os.getpid')]:
            call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
            self.assertEqual(call['targets'], [['external', target, '']])

    def test_duplicate_and_missing_argument_bindings_stay_unclassified(self):
        for actual, reason in [('time.monotonic, fn=os.getpid', 'duplicate_argument_binding'),
                               ('', 'argument_binding_mismatch')]:
            with self.subTest(actual=actual):
                graph = self.graph({'entry': 'import os, time\ndef f(fn):\n    fn()\nf(' + actual + ')\n'})
                self.assertTrue(any(row['reason'] == reason for row in graph['unclassified']))
                self.assertFalse(graph['source_audit_complete'])
        graph = self.graph({'entry': 'import os\nclass C:\n    def f(self):\n        self()\nc=C()\nc.f(self=os.getpid)\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'self()'))
        self.assertEqual({target[0] for target in call['targets']}, {'instance'})
        self.assertTrue(any(row['reason'] == 'duplicate_argument_binding' for row in graph['unclassified']))

    def test_unknown_expansion_keeps_uncertainty_without_receiver_alias(self):
        graph = self.graph({'entry': 'class C:\n    def f(self, value, *rest, flag=None, **kwargs):\n'
                            '        value()\nc=C()\nc.f(*unknown, **mapping)\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'value()'))
        self.assertEqual(call['targets'], [])
        self.assertTrue(any(row['reason'] == 'iteration_receiver_summary_required' for row in graph['unclassified']))
        self.assertTrue(any(row['reason'] == 'keyword_expansion_protocol_summary_required' for row in graph['unclassified']))

    def test_expansion_callbacks_exist_even_without_a_resolved_callee(self):
        graph = self.graph({'entry': 'import os\nclass I:\n    def __iter__(self):\n        return self\n'
                            '    def __next__(self):\n        return os.getpid()\nunknown(*I())\n'})
        self.assertTrue(any(row['method'] == '__next__' for row in graph['builtin_protocol_edges']))
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                       self.nodes(graph, 'Call', 'unknown(*I())')))
        self.assertTrue(any(row['reason'] == 'call_target_unresolved' for row in graph['unclassified']))

    def return_fact(self, graph, function):
        return next((row for row in graph['function_return_facts'] if '::' + function + '@' in row['function']), None)

    def test_future_annotations_preserve_source_without_executing_spelling(self):
        source = ('"module doc"\nfrom __future__ import annotations\n'
                  'import os\nvalue: os.getenv("owner")\n'
                  '@decorate\ndef f(arg: os.getenv("Q") = default()) -> registry[key()]:\n    pass\n')
        graph = self.graph({'entry': source})
        self.assertEqual(len(graph['annotation_inventory']), 3)
        self.assertEqual({row['mode'] for row in graph['annotation_inventory']}, {'stringified'})
        self.assertFalse(self.nodes(graph, 'Call', "os.getenv('owner')"))
        self.assertFalse(self.nodes(graph, 'Call', "os.getenv('Q')"))
        self.assertFalse(self.nodes(graph, 'Call', 'key()'))
        self.assertTrue(self.nodes(graph, 'Call', 'default()'))
        self.assertTrue(self.nodes(graph, 'decorated_definition'))
        self.assertFalse(graph['source_audit_complete'])

    def test_annotation_mode_is_per_module_and_inherited_by_nested_definitions(self):
        body = 'def outer():\n    def inner(arg: source()) -> result():\n        pass\n    return inner\n'
        graph = self.graph({'postponed': 'from __future__ import annotations\n' + body, 'ordinary': body})
        calls = [node for node in graph['nodes'] if node['kind'] == 'Call' and node['label'] in ('source()', 'result()')]
        self.assertEqual(len(calls), 2)
        self.assertEqual({node['path'] for node in calls}, {'proof_kernel/ordinary.py'})
        self.assertEqual({row['mode'] for row in graph['annotation_inventory']},
                         {'stringified', 'runtime_evaluation_required'})

    def test_local_annotations_skip_only_annotation_and_final_target_operation(self):
        body = ('def f():\n    local: forbidden()\n    receiver().attr: forbidden()\n'
                '    receiver()[index()]: forbidden()\n    assigned: forbidden() = value()\n')
        for prefix in ('', 'from __future__ import annotations\n'):
            with self.subTest(prefix=prefix):
                graph = self.graph({'entry': prefix + body})
                self.assertFalse(self.nodes(graph, 'Call', 'forbidden()'))
                self.assertEqual(len(self.nodes(graph, 'Call', 'receiver()')), 2)
                self.assertEqual(len(self.nodes(graph, 'Call', 'index()')), 1)
                self.assertEqual(len(self.nodes(graph, 'Call', 'value()')), 1)
                self.assertFalse(self.nodes(graph, 'uninitialized'))
                self.assertEqual({row['mode'] for row in graph['annotation_inventory']}, {'not_evaluated'})

    def test_annotation_only_declaration_does_not_overwrite_callable(self):
        graph = self.graph({'entry': 'def target():\n    return 7\nselected = target\nselected: int\nselected()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'selected()'))
        self.assertTrue(any('::target@' in target[1] for target in call['targets']))
        self.assertFalse(self.nodes(graph, 'uninitialized'))
        self.assertFalse(self.reachable(graph, self.nodes(graph, 'annotation_source'),
                                        self.nodes(graph, 'name_read', 'selected')))

    def test_annotation_read_and_aliased_evaluator_keep_deferred_input_obligations(self):
        source = ('from __future__ import annotations\nfrom typing import get_type_hints as inspect_types\n'
                  'def f(arg: dangerous()):\n    pass\n'
                  'alias = f\ninspect_types(alias)\ntext = alias.__annotations__\neval(text["arg"])\n')
        graph = self.graph({'entry': source})
        annotations = self.nodes(graph, 'annotation_source', 'dangerous()')
        for kind, label in [('Call', 'inspect_types(alias)'), ('Attribute', 'alias.__annotations__'), ('Call', "eval(text['arg'])")]:
            nodes = self.nodes(graph, kind, label)
            self.assertTrue(self.reachable(graph, annotations, nodes))
            self.assertTrue(any(row['node'] in nodes and row['reason'].startswith('annotation_') for row in graph['unclassified']))
        self.assertFalse(self.nodes(graph, 'Call', 'dangerous()'))
        self.assertFalse(graph['source_audit_complete'])

    def test_annotation_namespace_writes_remain_unproved(self):
        graph = self.graph({'entry': 'from __future__ import annotations\n__annotations__ = custom\nx: int\nclass C:\n    y: str\n'})
        stored = {row['node'] for row in graph['annotation_inventory']}
        obligations = {row['node'] for row in graph['unclassified'] if row['reason'] == 'annotation_storage_write_summary_required'}
        self.assertEqual(stored, obligations)

    def test_future_like_import_and_misplaced_future_do_not_suppress_execution(self):
        for prefix in ('import __future__\n', 'from somewhere import annotations\n', 'x = 1\nfrom __future__ import annotations\n'):
            with self.subTest(prefix=prefix):
                graph = self.graph({'entry': prefix + 'def f(arg: forbidden()):\n    pass\n'})
                self.assertTrue(self.nodes(graph, 'Call', 'forbidden()'))

    def test_annotation_spelling_is_not_an_input_to_the_assigned_value(self):
        graph = self.graph({'entry': 'from __future__ import annotations\nvalue: forbidden() = source()\nsink(value)\n'})
        self.assertFalse(self.nodes(graph, 'Call', 'forbidden()'))
        self.assertTrue(self.nodes(graph, 'Call', 'source()'))
        self.assertFalse(self.reachable(graph, self.nodes(graph, 'annotation_source'),
                                        self.nodes(graph, 'name_read', 'value')))

    def test_local_return_contracts_cover_branches_bare_returns_and_fallthrough(self):
        examples = [
            ('def f(flag):\n    if flag:\n        return 1\n', ['NoneType', 'int'], True),
            ('def f(flag):\n    if flag:\n        return 1\n    else:\n        return 2\n', ['int'], False),
            ('def f():\n    return\n', ['NoneType'], False),
            ('def f():\n    pass\n', ['NoneType'], True),
            ('def f():\n    return 1\n    return unknown()\n', ['int'], False)]
        for source, types, falls in examples:
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                self.assertEqual(self.return_fact(graph, 'f')['output_types'], types)
                self.assertEqual(self.return_inventory(graph, 'f')['falls_through'], falls)
                self.assertFalse(graph['source_audit_complete'])

    def test_finally_preserves_or_overrides_returns_and_can_remove_normal_return(self):
        cases = [
            ('try:\n        return unknown()\n    finally:\n        return 3', ['int']),
            ('try:\n        return 4\n    finally:\n        pass', ['int']),
            ('try:\n        return 4\n    finally:\n        if flag:\n            return "override"', ['int', 'str']),
            ('try:\n        return 4\n    finally:\n        raise ValueError()', None)]
        for body, expected in cases:
            with self.subTest(body=body):
                graph = self.graph({'entry': 'def f(flag):\n    ' + body + '\n'})
                fact = self.return_fact(graph, 'f')
                self.assertEqual(None if fact is None else fact['output_types'], expected)
                self.assertFalse(self.return_inventory(graph, 'f')['falls_through'])

    def test_exception_handlers_else_and_suppressed_errors_keep_all_normal_results(self):
        source = ('def f(value):\n    try:\n        return len(value)\n'
                  '    except ValueError:\n        pass\n')
        graph = self.graph({'entry': source})
        self.assertEqual(self.return_fact(graph, 'f')['output_types'], ['NoneType', 'int'])
        source = ('def f(flag):\n    try:\n        if flag:\n            raise ValueError()\n'
                  '    except ValueError:\n        return "error"\n    else:\n        return 0\n')
        graph = self.graph({'entry': source})
        self.assertEqual(self.return_fact(graph, 'f')['output_types'], ['int', 'str'])
        self.assertTrue(any(row['reason'] == 'exception_control_summary_required' for row in graph['unclassified']))

    def test_loop_zero_iteration_break_continue_and_nested_else_exits(self):
        cases = [
            ('def f(values):\n    for value in values:\n        return 1\n', ['NoneType', 'int']),
            ('def f(values):\n    for value in values:\n        break\n'
             '    else:\n        return 1\n    return "broken"\n', ['int', 'str']),
            ('def f(values):\n    for value in values:\n        continue\n'
             '    else:\n        return 1\n', ['int'])]
        for source, expected in cases:
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                self.assertEqual(self.return_fact(graph, 'f')['output_types'], expected)
        source = ('def f(values):\n    for value in values:\n'
                  '        for inner in ():\n            pass\n        else:\n            break\n'
                  '        return "unreachable"\n    else:\n        return 1\n    return "broken"\n')
        graph = self.graph({'entry': source})
        self.assertEqual({graph['nodes'][number]['label'] for number in self.return_inventory(graph, 'f')['inputs']},
                         {'1', "'broken'"})

    def test_multiple_context_entries_can_suppress_an_error_before_break(self):
        source = ('def f(first, second):\n    for value in [1]:\n'
                  '        with first, second:\n            break\n'
                  '        return "suppressed"\n    return 1\n')
        graph = self.graph({'entry': source})
        self.assertEqual(self.return_fact(graph, 'f')['output_types'], ['int', 'str'])
        self.assertTrue(any(row['reason'] == 'context_manager_summary_required' for row in graph['unclassified']))

    def test_owned_cpu_return_paths_match_the_derived_type_sets(self):
        import inspect
        import textwrap
        class BadLength:
            def __len__(self):
                raise ValueError('owned fixture')
        class Context:
            def __init__(self, fail=False):
                self.fail = fail
            def __enter__(self):
                if self.fail:
                    raise ValueError('owned entry fixture')
                return self
            def __exit__(self, *exc):
                return True
        def branch(flag):
            if flag:
                return 1
        def caught(value):
            try:
                return len(value)
            except ValueError:
                pass
        def loop(values):
            for value in values:
                break
            else:
                return 1
            return 'broken'
        def suppress(first, second):
            for value in [1]:
                with first, second:
                    break
                return 'suppressed'
            return 1
        fixtures = [(branch, [(True,), (False,)]), (caught, [([],), (BadLength(),)]),
                    (loop, [([],), ([1],)]), (suppress, [(Context(), Context()), (Context(), Context(True))])]
        for function, arguments in fixtures:
            with self.subTest(function=function.__name__):
                graph = self.graph({'entry': textwrap.dedent(inspect.getsource(function))})
                expected = self.return_fact(graph, function.__name__)['output_types']
                actual = sorted({type(function(*args)).__name__ for args in arguments})
                self.assertEqual(actual, expected)
        # Python 3.14 warns while compiling this deliberate native fixture.
        # Execute it in its own interpreter so both streams are captured,
        # rather than emitting a fixture warning before the closure CLI starts.
        source = 'def overridden():\n    try:\n        return object()\n    finally:\n        return 3\n'
        graph = self.graph({'entry': source})
        native = subprocess.run([sys.executable, '-B', '-c', source + 'print(type(overridden()).__name__)'],
                                capture_output=True, timeout=15)
        self.assertEqual(native.returncode, 0, native.stderr)
        self.assertEqual([native.stdout.decode().strip()], self.return_fact(graph, 'overridden')['output_types'])

    def test_generator_coroutine_and_async_generator_are_not_body_return_values(self):
        cases = [('def f():\n    return 7\n    yield 1\n', 'generator'),
                 ('async def f():\n    return 7\n', 'coroutine'),
                 ('async def f():\n    yield 1\n', 'async_generator')]
        for source, kind in cases:
            with self.subTest(kind=kind):
                graph = self.graph({'entry': source + 'result = f()\nvalue = result + 1\n'})
                self.assertEqual(self.return_inventory(graph, 'f')['suspension'], kind)
                self.assertIsNone(self.return_fact(graph, 'f'))
                nodes = self.nodes(graph, 'BinOp', 'result + 1')
                self.assertFalse(any(row['node'] in nodes for row in graph['primitive_effects']))
        graph = self.graph({'entry': 'import os\ndef f():\n    yield 1\n    return os.getpid\nresult = f()\nresult()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'result()'))
        self.assertNotIn(['external', 'os.getpid', ''], call['targets'])
        self.assertTrue(any(row['node'] == call['node'] and row['reason'] == 'callable_identity_unclassified:suspended_result'
                            for row in graph['unclassified']))

    def test_nested_bodies_and_enclosing_default_yields_have_distinct_scopes(self):
        plain = ('def outer():\n    def inner():\n        yield 1\n    return 2\n')
        graph = self.graph({'entry': plain})
        self.assertIsNone(self.return_inventory(graph, 'outer')['suspension'])
        self.assertEqual(self.return_fact(graph, 'outer')['output_types'], ['int'])
        for definition in ('def inner(value=(yield 1)):\n        pass',
                           'inner = lambda value=(yield 1): 2',
                           'class Inner((yield object)):\n        pass'):
            with self.subTest(definition=definition):
                graph = self.graph({'entry': 'def outer():\n    ' + definition + '\n    return 2\n'})
                self.assertEqual(self.return_inventory(graph, 'outer')['suspension'], 'generator')
                self.assertIsNone(self.return_fact(graph, 'outer'))

    def test_unknown_return_paths_and_recursive_contracts_stay_open(self):
        for source in ('def f(value):\n    return value\n',
                       'def f(flag):\n    if flag:\n        return 1\n    return unknown()\n',
                       'def f(value):\n    if value:\n        return 1\n    return f(value)\n'):
            with self.subTest(source=source):
                graph = self.graph({'entry': source + 'result = f(1)\nvalue = result + 1\n'})
                self.assertIsNone(self.return_fact(graph, 'f'))
                nodes = self.nodes(graph, 'BinOp', 'result + 1')
                self.assertFalse(any(row['node'] in nodes for row in graph['primitive_effects']))

    def test_local_call_types_require_closed_targets_and_keep_platform_dispatch(self):
        graph = self.graph({'entry': 'import os\ndef a():\n    return 1\ndef b():\n    return 2\n'
                            'fn = a if os.getpid() else b\nresult = fn() + 1\n'})
        facts = [row for row in graph['local_call_return_facts'] if row['node'] in self.nodes(graph, 'Call', 'fn()')]
        self.assertEqual(len(facts), 1)
        self.assertEqual(len(facts[0]['functions']), 2)
        self.assertEqual(facts[0]['output_facts'], ['type:int'])
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), self.nodes(graph, 'symbol', 'result')))
        graph = self.graph({'entry': 'def a():\n    return 1\nfn = a\nfn = unknown\nresult = fn() + 1\n'})
        self.assertFalse(any(row['node'] in self.nodes(graph, 'Call', 'fn()') for row in graph['local_call_return_facts']))

    def test_discarded_finally_return_cannot_supply_a_callable_alias(self):
        graph = self.graph({'entry': 'def a():\n    return 1\ndef b():\n    return 2\n'
                            'def choose():\n    try:\n        return a\n    finally:\n        return b\n'
                            'fn = choose()\nresult = fn() + 1\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
        self.assertEqual(len(call['targets']), 1)
        self.assertIn('::b@', call['targets'][0][1])
        self.assertTrue(any(row['node'] in self.nodes(graph, 'BinOp', 'fn() + 1') and row['output_types'] == ['int']
                            for row in graph['primitive_effects']))

    def test_returned_function_fact_can_resolve_a_later_local_call(self):
        graph = self.graph({'entry': 'def value():\n    return 3\ndef factory():\n    return value\n'
                            'selected = factory()\nresult = selected() + 1\n'})
        factory = self.return_fact(graph, 'factory')
        self.assertTrue(factory['output_facts'][0].startswith('function:proof_kernel/entry.py::value@'))
        self.assertEqual(factory['output_types'], [])
        self.assertTrue(any(row['node'] in self.nodes(graph, 'BinOp', 'selected() + 1') for row in graph['primitive_effects']))

    def test_primitive_operator_summaries_match_actual_builtin_result_types(self):
        # Only these owned constant examples execute. The graph parses text
        # and never evaluates a candidate expression to decide its effects.
        examples = [
            ('2 + 3', 2 + 3), ('True + False', True + False),
            ('True & False', True & False), ('True | 4', True | 4),
            ('7 / 2', 7 / 2), ('7 // 2', 7 // 2), ('7.0 % 2', 7.0 % 2),
            ('2 ** -1', 2 ** -1), ('(-1.0) ** 0.5', (-1.0) ** 0.5),
            ('2j + 3', 2j + 3), ('b"a" * 3', b'a' * 3),
            ('"a" + "b"', 'a' + 'b'), ('~4', ~4), ('not []', not []),
            ('1 < 2 <= 3', 1 < 2 <= 3), ('"a" in "cat"', 'a' in 'cat'),
            ('65 in b"ABC"', 65 in b'ABC'), ('f"{2 + 3:03d}"', f'{2 + 3:03d}')]
        import ast
        for expression, actual in examples:
            with self.subTest(expression=expression):
                graph = self.graph({'entry': 'value = ' + expression + '\n'})
                syntax = ast.parse(expression, mode='eval').body
                nodes = self.nodes(graph, type(syntax).__name__, ast.unparse(syntax))
                effects = [row for row in graph['primitive_effects'] if row['node'] in nodes and row['operation'] != 'truth_test']
                self.assertEqual(len(effects), 1)
                self.assertIn(type(actual).__name__, effects[0]['output_types'])
                self.assertFalse(any(row['node'] in nodes and row['reason'].startswith('operand_protocol_summary_required:')
                                     for row in graph['unclassified']))
                self.assertFalse(graph['source_audit_complete'])

    def test_identity_comparison_handles_unknown_objects_without_invoking_equality(self):
        graph = self.graph({'entry': 'import os\ndef same(unknown):\n    return unknown is os.getpid()\n'})
        nodes = self.nodes(graph, 'Compare', 'unknown is os.getpid()')
        effect = next(row for row in graph['primitive_effects'] if row['node'] in nodes)
        self.assertTrue(effect['identity_dependency'])
        self.assertEqual(effect['output_types'], ['bool'])
        self.assertEqual(effect['implicit_callbacks'], [])
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                       self.nodes(graph, 'return_slot', function='same')))
        rich = self.graph({'entry': 'def same(unknown):\n    return unknown == None\n'})
        self.assertTrue(any(row['reason'] == 'operand_protocol_summary_required:Compare' for row in rich['unclassified']))

    def test_primitive_type_proof_keeps_all_assignment_alternatives(self):
        for assignment in ('value = unknown()', 'value = Custom()', 'value = external'):
            with self.subTest(assignment=assignment):
                graph = self.graph({'entry': 'import os\nclass Custom:\n'
                                    '    def __add__(self, other):\n        return os.getpid()\n'
                                    'value = 1\n' + assignment + '\nresult = value + 2\n'})
                nodes = self.nodes(graph, 'BinOp', 'value + 2')
                self.assertFalse(any(row['node'] in nodes for row in graph['primitive_effects']))
                self.assertTrue(any(row['node'] in nodes and row['reason'] == 'operand_protocol_summary_required:BinOp'
                                    for row in graph['unclassified']))
        graph = self.graph({'entry': 'value = 1\nvalue = 2.0\nresult = value + 2\n'})
        effect = next(row for row in graph['primitive_effects'] if row['node'] in self.nodes(graph, 'BinOp', 'value + 2'))
        self.assertEqual(effect['output_types'], ['float', 'int'])

    def test_parameters_unknown_returns_fields_and_container_elements_are_not_exact_type_proof(self):
        sources = (
            'def f(value):\n    return value + 2\nf(1)\n',
            'def f(unknown):\n    return unknown\nvalue = f(1)\nresult = value + 2\n',
            'class Box:\n    value = 1\nvalue = Box().value\nresult = value + 2\n',
            'value = [1][0]\nresult = value + 2\n')
        for source in sources:
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                nodes = self.nodes(graph, 'BinOp', 'value + 2')
                self.assertTrue(any(row['node'] in nodes and row['reason'] == 'operand_protocol_summary_required:BinOp'
                                    for row in graph['unclassified']))

    def test_builtin_summaries_require_exact_callable_and_argument_bindings(self):
        graph = self.graph({'entry': 'size = len\nvalue = size([1, 2])\nresult = value + 2\n'
                            'from builtins import abs as magnitude\nvalue2 = magnitude(2j)\n'})
        effects = {row['operation']: row for row in graph['primitive_effects']}
        self.assertEqual(effects['builtins.len']['output_types'], ['int'])
        self.assertEqual(effects['builtins.abs']['output_types'], ['float'])
        self.assertFalse(any(row['reason'] == 'external_api_summary_required:builtins.len' for row in graph['unclassified']))
        for source in ('size = len\nsize = unknown\nsize([])\n',
                       'def len(value):\n    return value\nlen([])\n',
                       'len(unknown)\n', 'len(value=[])\n', 'len(*[[]])\n',
                       'class C(list):\n    def __len__(self):\n        return 9\nlen(C())\n'):
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                self.assertFalse(any(row['operation'] == 'builtins.len' for row in graph['primitive_effects']))

    def test_builtin_return_type_does_not_discharge_unknown_call_effects(self):
        graph = self.graph({'entry': 'def derive(unknown):\n'
                            '    count = len(unknown)\n'
                            '    identity = hash(unknown)\n'
                            '    if hasattr(unknown, "owner"):\n        return count + identity\n'
                            '    return bool(unknown)\n'})
        for name, expected in (('len', 'int'), ('hash', 'int'), ('hasattr', 'bool'), ('bool', 'bool')):
            fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'builtins.' + name)
            self.assertEqual(fact['condition'], 'successful_return')
            self.assertEqual(fact['output_types'], [expected])
            self.assertEqual(fact['unresolved_effect_obligation'], 'external_api_summary_required:builtins.' + name)
            self.assertIn({'node': fact['node'], 'reason': fact['unresolved_effect_obligation']}, graph['unclassified'])
        nodes = self.nodes(graph, 'BinOp', 'count + identity')
        self.assertTrue(any(row['node'] in nodes and row['output_types'] == ['int'] for row in graph['primitive_effects']))
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'symbol', 'unknown', 'derive'),
                                       self.nodes(graph, 'return_slot', function='derive')))

    def test_exact_container_methods_preserve_element_origin_through_alias_and_copy(self):
        graph = self.graph({'entry': 'import os\nxs = []\nadd = xs.append\nadd(os.getpid())\n'
                            'ys = xs.copy()\nys.reverse()\nys.extend((42,))\nys.insert(0, 17)\n'
                            'owner = ys[0]\nrecord = {"owner": owner}\nview = record.items()\nseq = list(view)\n'})
        effects = {row['operation']: row for row in graph['primitive_effects']}
        for name in ('list.append', 'list.copy', 'list.reverse', 'list.extend', 'list.insert',
                     'literal_dict', 'dict.items', 'builtins.list'):
            self.assertIn(name, effects)
            self.assertEqual(effects[name]['implicit_callbacks'], [])
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                       self.nodes(graph, 'symbol', 'seq')))
        self.assertFalse(graph['source_audit_complete'])

    def test_exact_dictionary_views_do_not_authorize_key_or_value_callbacks(self):
        graph = self.graph({'entry': 'record = {"key": unknown}\n'
                            'keys = record.keys()\nvalues = record.values()\nitems = record.items()\n'
                            'sizes = (len(keys), len(values), len(items))\nrecord.get(unknown)\nrecord.copy()\n'})
        effects = [row['operation'] for row in graph['primitive_effects']]
        for name in ('dict.keys', 'dict.values', 'dict.items'):
            self.assertIn(name, effects)
        self.assertEqual(effects.count('builtins.len'), 3)
        for name in ('dict.get', 'dict.copy'):
            self.assertNotIn(name, effects)
            self.assertTrue(any(row['reason'] == 'container_element_protocol_summary_required:' + name
                                for row in graph['unclassified']))

    def test_container_effects_require_closed_receiver_and_bound_method_aliases(self):
        examples = ('xs = []\nxs = unknown\nxs.append(1)\n',
                    'xs = []\nadd = xs.append\nadd = unknown\nadd(1)\n',
                    'class Child(list):\n    def append(self, value):\n        forbidden(value)\nChild().append(1)\n',
                    'def use(xs):\n    xs.append(1)\nuse([])\n',
                    'xs = []\nadd = xs.append\nxs = unknown\nadd(1)\n')
        for source in examples:
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                self.assertFalse(any(row['operation'] == 'list.append' for row in graph['primitive_effects']))

    def test_multiple_exact_method_receivers_keep_both_input_edges(self):
        graph = self.graph({'entry': 'left = []\nright = []\nadd = left.append if flag else right.append\nadd(value)\n'})
        effect = next(row for row in graph['primitive_effects'] if row['operation'] == 'list.append')
        self.assertEqual(len(effect['receiver_nodes']), 2)
        self.assertTrue(set(effect['receiver_nodes']) <= set(effect['inputs']))
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'symbol', 'value'),
                                       self.nodes(graph, 'List')))

    def test_container_arity_expansion_and_custom_protocol_arguments_stay_open(self):
        for expression in ('xs.append()', 'xs.append(1, 2)', 'xs.append(object=1)', 'xs.append(*unknown)',
                           'xs.extend(unknown)', 'xs.insert(unknown, 1)', 'xs.clear()', 'xs.pop()',
                           'xs.__setitem__(0, unknown)'):
            with self.subTest(expression=expression):
                graph = self.graph({'entry': 'xs = [unknown]\n' + expression + '\n'})
                calls = self.nodes(graph, 'Call', expression)
                self.assertFalse(any(row['node'] in calls for row in graph['primitive_effects']))
                self.assertTrue(any(row['node'] in calls for row in graph['unclassified']))

    def test_constructor_success_types_do_not_erase_input_hooks(self):
        graph = self.graph({'entry': 'xs = list(unknown)\nsize = len(xs)\n'
                            'record = dict(unknown)\nkeys = record.keys()\nset(unknown)\nfrozenset(unknown)\n'})
        effects = {row['operation'] for row in graph['primitive_effects']}
        self.assertIn('builtins.len', effects)
        self.assertIn('dict.keys', effects)
        for name in ('list', 'dict', 'set', 'frozenset'):
            self.assertNotIn('builtins.' + name, effects)
            fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'builtins.' + name)
            self.assertEqual(fact['output_types'], [name])
            self.assertEqual(fact['unresolved_effect_obligation'], 'external_api_summary_required:builtins.' + name)

    def test_empty_constructors_and_exact_builtin_iteration_have_closed_effects(self):
        graph = self.graph({'entry': 'a = list()\nb = tuple()\nc = dict()\nd = set()\ne = frozenset()\n'
                            'list(c)\nlist(d)\ntuple(e)\nlist(range(3))\ntuple("hi")\nlist(b"hi")\n'})
        effects = [row['operation'] for row in graph['primitive_effects']]
        for name in ('list', 'tuple', 'dict', 'set', 'frozenset'):
            self.assertIn('builtins.' + name, effects)
        self.assertEqual(effects.count('builtins.list'), 5)
        self.assertEqual(effects.count('builtins.tuple'), 3)

    def test_constructor_aliases_cannot_close_shadowed_or_partial_callables(self):
        for source in ('make = list\nmake = unknown\nmake()\n',
                       'def list():\n    return unknown\nlist()\n',
                       'from external import list\nlist()\n'):
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                self.assertFalse(any(row['operation'] == 'builtins.list' for row in graph['primitive_effects']))

    def test_literal_dict_unique_builtin_keys_and_scalar_sets_close_only_construction(self):
        graph = self.graph({'entry': 'empty = {}\nrecord = {"a": unknown, 3: other, None: unknown}\n'
                            'values = {1, 2, "x", None}\n'})
        effects = [row['operation'] for row in graph['primitive_effects']]
        self.assertEqual(effects.count('literal_dict'), 2)
        self.assertEqual(effects.count('literal_set'), 1)
        self.assertTrue(any(row['reason'] == 'name_binding_missing' for row in graph['unclassified']))

    def test_literal_duplicate_keys_expansions_and_custom_hashes_remain_open(self):
        for expression, operation in (("{'x': first, 'x': second}", 'literal_dict'),
                                       ('{True: first, 1: second}', 'literal_dict'),
                                       ('{1: first, 1.0: second}', 'literal_dict'),
                                       ('{unknown: 1}', 'literal_dict'), ('{**{}}', 'literal_dict'),
                                       ('{unknown}', 'literal_set'), ('{*[1]}', 'literal_set')):
            with self.subTest(expression=expression):
                graph = self.graph({'entry': 'result = ' + expression + '\n'})
                outer = min(self.nodes(graph, 'Dict' if operation == 'literal_dict' else 'Set'))
                self.assertFalse(any(row['node'] == outer and row['operation'] == operation for row in graph['primitive_effects']))
                self.assertTrue(any(row['node'] == outer and row['reason'].startswith('container_construction_protocol_summary_required:')
                                    for row in graph['unclassified']))

    def test_custom_sequence_index_retains_callback_input_and_pending_effect(self):
        graph = self.graph({'entry': 'import os\nclass Index:\n'
                            '    def __index__(self):\n        return os.getpid()\n'
                            'owner = [1, 2][Index()]\n'})
        selected = self.nodes(graph, 'Subscript', '[1, 2][Index()]')
        callbacks = [row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'sequence_index']
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(callbacks[0]['method'], '__index__')
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                       self.nodes(graph, 'symbol', 'owner')))
        self.assertTrue(any(row['node'] in selected and row['reason'] == 'subscript_receiver_summary_required'
                            for row in graph['unclassified']))
        self.assertFalse(any(row['node'] in selected for row in graph['primitive_effects']))

    def test_sequence_slice_bounds_and_list_method_indexes_trace_slots(self):
        graph = self.graph({'entry': 'import os\nclass Index:\n'
                            '    def __index__(self):\n        return os.getpid()\n'
                            'xs = [1, 2]\nvalue = xs[Index():Index():Index()]\n'
                            'xs.insert(Index(), 1)\nxs.pop(Index())\nxs[Index()] = 1\n'})
        callbacks = [row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'sequence_index']
        self.assertEqual(len(callbacks), 6)
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                       self.nodes(graph, 'symbol', 'value')))
        self.assertTrue(any(row['reason'] == 'subscript_receiver_summary_required' for row in graph['unclassified']))

    def test_custom_index_uses_type_slot_and_never_returns_a_callable_alias(self):
        graph = self.graph({'entry': 'def forbidden():\n    pass\nclass Index:\n'
                            '    def __init__(self):\n        self.__index__ = forbidden\n'
                            '    def __index__(self):\n        return forbidden\n'
                            'selected = [1][Index()]\nselected()\n'})
        callback = next(row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'sequence_index')
        call = next(row for row in graph['calls'] if row['node'] == callback['callback_node'])
        self.assertTrue(all('Index.__index__@' in target[1] for target in call['targets']))
        selected = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'selected()'))
        self.assertFalse(any('::forbidden@' in target[1] for target in selected['targets']))

    def test_sequence_selector_summary_requires_complete_receiver_and_index(self):
        for source in ('xs = [1]\nxs = unknown\nvalue = xs[0]\n',
                       'xs = [1]\nvalue = xs[unknown]\n',
                       'xs = [1]\nvalue = xs[:unknown]\n',
                       'record = {"a": 1}\nvalue = record["a"]\n'):
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                nodes = self.nodes(graph, 'Subscript')
                self.assertTrue(any(row['node'] in nodes and row['reason'] == 'subscript_receiver_summary_required'
                                    for row in graph['unclassified']))
                self.assertFalse(any(row['node'] in nodes for row in graph['primitive_effects']))

    def test_exact_sequence_read_and_slice_effects_do_not_invent_element_types(self):
        graph = self.graph({'entry': 'xs = [unknown]\na = xs[0]\nb = xs[:]\n'
                            'c = (unknown,)[True]\nd = range(4)[1]\ne = range(4)[:2]\n'})
        for label, output in (('xs[0]', []), ('xs[:]', ['list']), ('(unknown,)[True]', []),
                              ('range(4)[1]', ['int']), ('range(4)[:2]', ['range'])):
            nodes = self.nodes(graph, 'Subscript', label)
            effect = next(row for row in graph['primitive_effects'] if row['node'] in nodes)
            self.assertEqual(effect['output_types'], output)
            self.assertFalse(any(row['node'] in nodes and row['reason'] == 'subscript_receiver_summary_required'
                                 for row in graph['unclassified']))

    def test_sequence_writes_keep_replacement_and_finalizer_effects_open(self):
        graph = self.graph({'entry': 'xs = [unknown]\nxs[0] = 1\nxs[:] = []\n'})
        obligations = [row for row in graph['unclassified'] if row['reason'] == 'subscript_receiver_summary_required']
        self.assertEqual(len(obligations), 2)
        self.assertFalse(any(row['operation'] == 'builtin_sequence_subscript' for row in graph['primitive_effects']))

    def test_native_container_iteration_has_effect_proof_without_unknown_item_types(self):
        graph = self.graph({'entry': 'for a in [unknown]:\n    consume(a)\n'
                            'for b in {"a": unknown}.items():\n    consume(b)\n'})
        effects = [row for row in graph['primitive_effects'] if row['operation'] == 'builtin_container_iteration']
        self.assertEqual(len(effects), 2)
        self.assertEqual(sorted(row['output_types'] for row in effects), [[], ['tuple']])

    def test_partial_container_iteration_cannot_hide_unknown_iterator(self):
        graph = self.graph({'entry': 'values = [1]\nvalues = unknown\nfor value in values:\n    consume(value)\n'})
        self.assertTrue(any(row['reason'] == 'iteration_receiver_summary_required' for row in graph['unclassified']))
        self.assertFalse(any(row['operation'] == 'builtin_container_iteration' for row in graph['primitive_effects']))

    def test_custom_iterator_traces_iter_next_and_yielded_callable_identity(self):
        graph = self.graph({'entry': 'import os\ndef emitted():\n    return os.getpid()\n'
                            'class Iterator:\n'
                            '    def __iter__(self):\n        return self\n'
                            '    def __next__(self):\n        return emitted\n'
                            'for call in Iterator():\n    owner = call()\n'})
        callbacks = graph['builtin_protocol_edges']
        self.assertEqual({row['builtin'] for row in callbacks}, {'iteration', 'iteration_next'})
        target = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'call()'))
        self.assertTrue(any('::emitted@' in row[1] for row in target['targets']))
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), self.nodes(graph, 'symbol', 'owner')))
        self.assertTrue(any(row['reason'] == 'iteration_receiver_summary_required' for row in graph['unclassified']))

    def test_index_descriptor_and_sequence_iteration_fallback_remain_unproved(self):
        graph = self.graph({'entry': 'class Index:\n'
                            '    @property\n    def __index__(self):\n        return unknown\n'
                            'selected = [1][Index()]\nclass Sequence:\n'
                            '    def __getitem__(self, index):\n        return unknown\n'
                            'for value in Sequence():\n    consume(value)\n'})
        reasons = {row['reason'] for row in graph['unclassified']}
        self.assertIn('special_method_descriptor_summary_required:sequence_index.__index__', reasons)
        self.assertIn('special_method_binding_summary_required:iteration.__iter__', reasons)
        self.assertIn('iteration_receiver_summary_required', reasons)

    def test_dictionary_hash_callback_reaches_selected_owner(self):
        graph = self.graph({'entry': 'import os\nclass Key:\n'
                            '    def __hash__(self):\n        return os.getpid() % 2\n'
                            '    def __eq__(self, other):\n        return True\n'
                            'table = {0: "A", 1: "B"}\nowner = table[Key()]\n'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                       self.nodes(graph, 'symbol', 'owner')))
        callbacks = [row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'dictionary_hash']
        self.assertEqual(len(callbacks), 1)
        self.assertIn('Key.__hash__@', callbacks[0]['target_definition'])
        self.assertTrue(any(row['reason'] == 'subscript_receiver_summary_required' for row in graph['unclassified']))

    def test_dictionary_equality_binds_the_actual_lookup_argument(self):
        graph = self.graph({'entry': 'import os\nclass Key:\n'
                            '    def __hash__(self):\n        return 0\n'
                            '    def __eq__(self, other):\n        return other == 0\n'
                            'table = {Key(): "A"}\nowner = table[os.getpid()]\n'})
        destination = self.nodes(graph, 'Subscript', 'table[os.getpid()]')
        callback = next(row for row in graph['builtin_protocol_edges']
                        if row['builtin'] == 'dictionary_equal' and row['builtin_node'] in destination)
        self.assertEqual(set(callback['argument_nodes']), self.nodes(graph, 'Call', 'os.getpid()'))
        call = next(row for row in graph['calls'] if row['node'] == callback['callback_node'])
        self.assertTrue(any(edge['kind'] == 'argument' and edge['source'] in callback['argument_nodes']
                            and graph['nodes'][edge['target']]['label'] == 'other' for edge in graph['edges']))
        self.assertTrue(any('Key.__eq__@' in row[1] for row in call['targets']))

    def test_dictionary_reflected_equality_reaches_selected_owner(self):
        graph = self.graph({'entry': 'import os\nclass Key:\n'
                            '    def __hash__(self):\n        return 0\n'
                            '    def __eq__(self, other):\n        return os.getpid() % 2 == other\n'
                            'table = {0: "A"}\nowner = table[Key()]\n'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), self.nodes(graph, 'symbol', 'owner')))
        callback = next(row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'dictionary_reflected_equal')
        self.assertTrue(callback['argument_nodes'])

    def test_dictionary_equality_truth_conversion_traces_bool_and_len_slots(self):
        for method in ('__bool__', '__len__'):
            with self.subTest(method=method):
                graph = self.graph({'entry': 'import os\nclass Verdict:\n'
                                    '    def ' + method + '(self):\n        return os.getpid()\n'
                                    'class Key:\n    def __hash__(self):\n        return 0\n'
                                    '    def __eq__(self, other):\n        return Verdict()\n'
                                    'table = {0: "A"}\nowner = table[Key()]\n'})
                callbacks = [row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'dictionary_truth']
                self.assertTrue(callbacks)
                self.assertEqual({row['method'] for row in callbacks}, {method})
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), self.nodes(graph, 'symbol', 'owner')))

    def test_dictionary_callback_results_do_not_become_selected_callable_aliases(self):
        graph = self.graph({'entry': 'def forbidden():\n    pass\ndef selected_value():\n    pass\n'
                            'class Key:\n    def __hash__(self):\n        return forbidden\n'
                            '    def __eq__(self, other):\n        return forbidden\n'
                            'table = {0: selected_value}\nselected = table[Key()]\nselected()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'selected()'))
        self.assertTrue(any('::selected_value@' in target[1] for target in call['targets']))
        self.assertFalse(any('::forbidden@' in target[1] for target in call['targets']))

    def test_dictionary_hash_slot_bypasses_instance_attribute_shadowing(self):
        graph = self.graph({'entry': 'def forbidden():\n    pass\nclass Key:\n'
                            '    def __init__(self):\n        self.__hash__ = forbidden\n'
                            '    def __hash__(self):\n        return 0\n'
                            'table = {0: "A"}\nowner = table[Key()]\n'})
        callback = next(row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'dictionary_hash')
        call = next(row for row in graph['calls'] if row['node'] == callback['callback_node'])
        self.assertTrue(all('Key.__hash__@' in target[1] for target in call['targets']))

    def test_dictionary_construction_methods_and_writes_trace_key_hashing(self):
        graph = self.graph({'entry': 'class Key:\n    def __hash__(self):\n        return unknown\n'
                            'table = {Key(): "A"}\na = table.get(Key())\nb = table.__getitem__(Key())\n'
                            'c = table.setdefault(Key(), "B")\nd = table.pop(Key())\ntable[Key()] = "C"\n'})
        callbacks = [row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'dictionary_hash']
        self.assertEqual(len(callbacks), 6)
        self.assertFalse(graph['source_audit_complete'])
        self.assertTrue(any(row['reason'].startswith('container_element_protocol_summary_required:dict.') for row in graph['unclassified']))

    def test_dictionary_builtin_keys_do_not_invent_callbacks_or_close_unproved_state(self):
        graph = self.graph({'entry': 'table = {0: unknown, "name": other}\na = table[0]\nb = table.get("name")\n'})
        self.assertFalse(any(row['builtin'].startswith('dictionary_') for row in graph['builtin_protocol_edges']))
        self.assertTrue(any(row['reason'] == 'subscript_receiver_summary_required' for row in graph['unclassified']))
        self.assertFalse(any(row['node'] in self.nodes(graph, 'Subscript') for row in graph['primitive_effects']))

    def test_dictionary_descriptors_and_subclasses_keep_dispatch_obligations(self):
        graph = self.graph({'entry': 'class Key:\n    @property\n    def __hash__(self):\n        return unknown\n'
                            'class Table(dict):\n    def __missing__(self, key):\n        return unknown\n'
                            'a = {0: "A"}[Key()]\nb = Table()[0]\n'})
        reasons = {row['reason'] for row in graph['unclassified']}
        self.assertIn('special_method_descriptor_summary_required:dictionary_hash.__hash__', reasons)
        self.assertIn('subscript_receiver_summary_required', reasons)
        self.assertFalse(graph['source_audit_complete'])

    def test_json_nested_values_and_mapping_methods_keep_raw_input(self):
        graph = self.graph({'entry': 'import json, os\nvalue = json.loads(os.getenv("RAW"))\n'
                            'owner = value["nested"].get("owner")\nrows = value.items()\n'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', "os.getenv('RAW')"), self.nodes(graph, 'symbol', 'owner')))
        apis = {r['api'] for r in graph['json_contract_inventory']}
        self.assertTrue({'json.loads', 'json_value.subscript', 'json_value.get', 'json_value.items'} <= apis)
        self.assertTrue(all(r['classification'] == 'conditional_possible_branch' for r in graph['json_contract_inventory']))
        self.assertFalse(graph['source_audit_complete'])

    def test_json_starred_unpack_preserves_input_nodes_and_open_shape(self):
        for target in ('head, *tail', '*head, tail', 'head, *middle, tail'):
            with self.subTest(target=target):
                graph = self.graph({'entry': 'import json, os\n' + target +
                                    ' = json.loads(os.getenv("RAW"))\n'})
                selectors = self.nodes(graph, 'unpack_selector')
                self.assertEqual(len(selectors), len(target.split(',')))
                nodes = {n['id'] for n in graph['nodes']}
                rows = [r for r in graph['json_contract_inventory'] if r['api'] == 'json_value.subscript']
                self.assertEqual(len(rows), len(selectors))
                self.assertTrue(all(set(r['inputs']) <= nodes and None not in r['inputs'] for r in rows))
                self.assertTrue(all(any(n in r['inputs'] for r in rows) for n in selectors))
                starts = self.nodes(graph, 'Call', "os.getenv('RAW')")
                for name in target.replace('*', '').replace(' ', '').split(','):
                    self.assertTrue(self.reachable(graph, starts, self.nodes(graph, 'symbol', name)))
                self.assertTrue(all(self.reachable(graph, starts, {n}) for n in selectors))
                self.assertEqual(sum(r['reason'] == 'starred_unpack_shape_summary_required'
                                     for r in graph['unclassified']), len(selectors))
                self.assertFalse(graph['source_audit_complete'])

    def test_json_nested_starred_unpack_keeps_each_source_dependency(self):
        graph = self.graph({'entry': 'import json\n(first, *rest), last = json.loads(raw)\n'
                            'owner = rest\n'})
        self.assertEqual(len(self.nodes(graph, 'unpack_selector')), 2)
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'symbol', 'raw'), self.nodes(graph, 'symbol', 'owner')))
        self.assertTrue(all(None not in r['inputs'] for r in graph['json_contract_inventory']))
        self.assertFalse(graph['source_audit_complete'])

    def test_json_literal_none_selector_is_distinct_from_unknown_unpack_shape(self):
        graph = self.graph({'entry': 'import json\nvalue = json.loads(raw)\nowner = value[None]\n'})
        self.assertFalse(self.nodes(graph, 'unpack_selector'))
        row = next(r for r in graph['json_contract_inventory'] if r['api'] == 'json_value.subscript')
        self.assertTrue(self.nodes(graph, 'Constant', 'None') & set(row['inputs']))
        self.assertNotIn(None, row['inputs'])
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'symbol', 'raw'), self.nodes(graph, 'symbol', 'owner')))

    def test_starred_unpack_unknown_position_does_not_select_a_fixed_callable(self):
        graph = self.graph({'entry': 'def left():pass\ndef right():pass\n'
                            'head, *tail = (left, right)\nhead()\n'})
        call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'head()'))
        self.assertTrue(any('::left@' in t[1] for t in call['targets']))
        self.assertTrue(any('::right@' in t[1] for t in call['targets']))
        self.assertTrue(any(r['reason'] == 'starred_unpack_shape_summary_required' for r in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])

    def test_json_pairs_hook_return_can_be_callable_at_root_or_nested_value(self):
        graph = self.graph({'entry': 'import json, os\ndef hook(pairs):\n    return os.getpid\n'
                            'value = json.loads(raw, object_pairs_hook=hook)\nvalue()\nvalue[0]()\n'})
        for label in ('value()', 'value[0]()'):
            call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', label))
            self.assertTrue(any(t[:2] == ['external', 'os.getpid'] for t in call['targets']))
        row = next(r for r in graph['json_callback_inventory'] if r['name'] == 'object_pairs_hook')
        self.assertTrue(row['return_identity'])
        self.assertTrue(any(e['kind'] == 'json_pair_key' for e in graph['edges']))
        self.assertTrue(any(e['kind'] == 'json_pair_value' for e in graph['edges']))

    def test_json_text_input_does_not_become_a_callable_alias(self):
        graph = self.graph({'entry': 'import json\ndef forbidden():\n    pass\n'
                            'value = json.loads(forbidden)\nvalue()\nvalue[0]()\n'})
        for label in ('value()', 'value[0]()'):
            call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', label))
            self.assertFalse(any('::forbidden@' in t[1] for t in call['targets']))
        self.assertTrue(any(r['reason'] == 'json_effects_summary_required:json.loads' for r in graph['unclassified']))

    def test_json_numeric_hooks_preserve_lexeme_and_arbitrary_return(self):
        for keyword in ('parse_int', 'parse_float', 'parse_constant'):
            with self.subTest(keyword=keyword):
                graph = self.graph({'entry': 'import json, os\ndef hook(text):\n    return os.getpid\n'
                                    'value = json.loads(raw, ' + keyword + '=hook)\nvalue()\n'})
                call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'value()'))
                self.assertTrue(any(t[:2] == ['external', 'os.getpid'] for t in call['targets']))
                row = next(r for r in graph['json_callback_inventory'] if r['name'] == keyword)
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'symbol', 'raw'), {row['argument_node']}))

    def test_json_object_hook_precedence_remains_a_selection_obligation(self):
        graph = self.graph({'entry': 'import json\nvalue = json.loads(raw, object_pairs_hook=unknown_pairs, object_hook=unknown_object)\n'})
        row = next(r for r in graph['json_callback_inventory'] if r['name'] == 'object_hook')
        self.assertEqual(row['selection_precondition'], 'object_pairs_hook_absent_or_None')
        self.assertTrue(any(r['reason'] == 'json_callback_selection_summary_required:object_hook' for r in graph['unclassified']))
        without = self.graph({'entry': 'import json\nvalue = json.loads(raw, object_pairs_hook=None, object_hook=None)\n'})
        self.assertEqual(without['json_callback_inventory'], [])

    def test_json_file_input_reaches_actual_stream_write(self):
        graph = self.graph({'entry': 'import json\nwith open("/in", "rb") as source:\n'
                            '    value = json.load(source)\nwith open("/out", "w") as dest:\n    json.dump(value, dest)\n'})
        read = next(r for r in graph['stream_contract_inventory'] if r['api'] == 'stream.read')
        write = next(r for r in graph['stream_contract_inventory'] if r['api'] == 'stream.write')
        self.assertTrue(self.reachable(graph, {read['effects']['external_read']}, {write['effects']['external_write']}))
        labels = {n['label'] for n in graph['nodes'] if n['kind'] == 'implicit_call'}
        self.assertTrue({'json.file.read', 'json.file.write'} <= labels)

    def test_json_encoder_default_sees_nested_values_but_does_not_alias_output(self):
        graph = self.graph({'entry': 'import json, os\ndef selected():\n    return os.getpid()\n'
                            'def default(value):\n    return value()\n'
                            'text = json.dumps({"key": selected}, default=default)\ntext()\n'})
        invoked = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'value()'))
        self.assertTrue(any('::selected@' in t[1] for t in invoked['targets']))
        encoded = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'text()'))
        self.assertFalse(any('::selected@' in t[1] for t in encoded['targets']))
        row = next(r for r in graph['json_callback_inventory'] if r['name'] == 'default')
        self.assertFalse(row['return_identity'])

    def test_json_custom_decoder_can_return_non_json_callable(self):
        graph = self.graph({'entry': 'import json, os\nclass Decoder:\n    def decode(self, text):\n        return os.getpid\n'
                            'value = json.loads(raw, cls=Decoder)\nvalue()\n'})
        call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'value()'))
        self.assertTrue(any(t[:2] == ['external', 'os.getpid'] for t in call['targets']))
        self.assertTrue(any(r['reason'] == 'json_custom_class_dispatch_summary_required' for r in graph['unclassified']))

    def test_json_custom_encoder_result_preserves_callable_identity(self):
        graph = self.graph({'entry': 'import json, os\nclass Encoder:\n    def encode(self, obj):\n        return os.getpid\n'
                            'value = json.dumps(raw, cls=Encoder)\nvalue()\n'})
        call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'value()'))
        self.assertTrue(any(t[:2] == ['external', 'os.getpid'] for t in call['targets']))

    def test_json_custom_chunks_reach_custom_writer_as_values(self):
        graph = self.graph({'entry': 'import json, os\nclass Encoder:\n    def iterencode(self, obj):\n        return [os.getpid]\n'
                            'class Writer:\n    def write(self, chunk):\n        return chunk()\njson.dump(raw, Writer(), cls=Encoder)\n'})
        call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'chunk()'))
        self.assertTrue(any(t[:2] == ['external', 'os.getpid'] for t in call['targets']))

    def test_json_rebinding_expanded_arguments_and_local_module_stay_open(self):
        graph = self.graph({'entry': 'import json\nload = json.loads\nload = unknown\nvalue = load(raw, **hooks)\n'})
        self.assertTrue(any(r['reason'] == 'json_expanded_argument_summary_required' for r in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])
        local = self.graph({'entry': 'import json\njson.loads(raw)\n', 'json': 'def loads(value):\n    return value\n'})
        self.assertEqual(local['json_contract_inventory'], [])

    def test_json_written_member_retains_callable_alias(self):
        graph = self.graph({'entry': 'import json, os\nvalue = json.loads(raw)\nvalue["callback"] = os.getpid\n'
                            'value["callback"]()\n'})
        call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', "value['callback']()"))
        self.assertTrue(any(t[:2] == ['external', 'os.getpid'] for t in call['targets']))
        self.assertTrue(any(r['reason'] == 'json_selector_and_mutation_summary_required' for r in graph['unclassified']))

    def test_json_unknown_mutator_inputs_survive_container_key_escape(self):
        for argument in ('value', '[value]', '{value: 0}', 'holder'):
            with self.subTest(argument=argument):
                graph = self.graph({'entry': 'import json, os\nclass Holder:\n    pass\nvalue = json.loads(raw)\n'
                                    'holder = Holder()\nholder.value = value\nmutate(' + argument + ', os.getpid())\ntext = json.dumps(value)\n'})
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), self.nodes(graph, 'symbol', 'text')))
                self.assertTrue(any(r['reason'] == 'json_escape_effects_summary_required' for r in graph['unclassified']))

    def test_stream_path_open_context_keeps_file_input_and_receiver(self):
        graph = self.graph({'entry': 'import os\nfrom pathlib import Path\n'
                            'with Path(os.getenv("FILE")).open("rb") as f:\n    raw = f.read()\n'})
        row = next(r for r in graph['stream_contract_inventory'] if r['api'] == 'stream.read')
        self.assertTrue(self.reachable(graph, {row['effects']['external_read']}, self.nodes(graph, 'symbol', 'raw')))
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', "os.getenv('FILE')"), {row['node']}))
        self.assertTrue(any(r['api'] == 'stream.__enter__' for r in graph['stream_contract_inventory']))
        self.assertTrue(any(r['api'] == 'stream.__exit__' for r in graph['stream_contract_inventory']))
        self.assertFalse(graph['source_audit_complete'])

    def test_stream_write_and_context_exit_keep_payload_and_exception_inputs(self):
        graph = self.graph({'entry': 'import os\nwith open("/record", "wb") as f:\n'
                            '    count = f.write(os.urandom(8))\n    raise ValueError(os.getpid())\n'})
        write = next(r for r in graph['stream_contract_inventory'] if r['api'] == 'stream.write')
        exited = next(r for r in graph['stream_contract_inventory'] if r['api'] == 'stream.__exit__')
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.urandom(8)'), {write['effects']['external_write']}))
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), {exited['effects']['external_write']}))
        self.assertTrue(any(r['reason'] == 'context_exception_suppression_summary_required' for r in graph['unclassified']))

    def test_stream_memory_state_carries_writes_without_inventing_file_input(self):
        graph = self.graph({'entry': 'import io, os\nf = io.BytesIO(b"initial")\n'
                            'f.write(os.urandom(4))\nf.seek(0)\nraw = f.read()\n'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.urandom(4)'), self.nodes(graph, 'symbol', 'raw')))
        self.assertTrue(all(r['backend'] == 'memory' and not r['effects'] for r in graph['stream_contract_inventory']))
        self.assertTrue(any(r['reason'] == 'stream_lifecycle_summary_required' for r in graph['unclassified']))

    def test_stream_opener_callback_returns_into_handle_provenance(self):
        graph = self.graph({'entry': 'import os\ndef choose(path, flags):\n    return os.getpid()\n'
                            'f = open("/record", "rb", opener=choose)\nraw = f.read()\n'})
        self.assertTrue(any(node['kind'] == 'implicit_call' and node['label'] == 'builtins.open.opener' for node in graph['nodes']))
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), self.nodes(graph, 'symbol', 'raw')))
        self.assertTrue(any(r['reason'] == 'stream_opener_dispatch_summary_required' for r in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])

    def test_stream_shadowed_and_mixed_open_receivers_do_not_close_effects(self):
        graph = self.graph({'entry': 'class Other:\n    def read(self):\n        return unknown\n'
                            'f = open("/x")\nf = Other()\nf = unresolved\nraw = f.read()\n'})
        call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'f.read()'))
        self.assertTrue(any(t[0] == 'stream_method' for t in call['targets']))
        self.assertTrue(any(t[0] == 'bound' and '.read@' in t[1] for t in call['targets']))
        self.assertFalse(any(r['node'] == call['node'] for r in graph['primitive_effects']))
        self.assertTrue(any(r['reason'] == 'attribute_receiver_summary_required:read' for r in graph['unclassified']))
        shadowed = self.graph({'entry': 'def open(path):\n    return unknown\nf = open("/x")\nf.read()\n'})
        self.assertEqual(shadowed['stream_contract_inventory'], [])

    def test_stream_async_context_does_not_borrow_synchronous_enter_identity(self):
        graph = self.graph({'entry': 'async def work():\n    async with open("/x") as f:\n        f.read()\n'})
        call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'f.read()'))
        self.assertFalse(any(t[0] == 'stream_method' for t in call['targets']))
        self.assertTrue(any(r['reason'] == 'stream_async_context_summary_required' for r in graph['unclassified']))

    def test_stream_iteration_reads_data_without_filename_callable_alias(self):
        graph = self.graph({'entry': 'def forbidden():\n    pass\nf = open(forbidden)\n'
                            'for line in f:\n    selected = line\n    line()\n'})
        row = next(r for r in graph['stream_contract_inventory'] if r['api'] == 'stream.iteration')
        self.assertTrue(self.reachable(graph, {row['effects']['external_read']}, self.nodes(graph, 'symbol', 'selected')))
        call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'line()'))
        self.assertFalse(any('::forbidden@' in t[1] for t in call['targets']))
        self.assertTrue(any(r['reason'] == 'stream_iteration_lifecycle_summary_required' for r in graph['unclassified']))

    def test_stream_private_write_and_escaped_mutator_reach_later_reads(self):
        for mutation in ('f.private = os.getpid()', 'mutate(f, os.getpid())',
                         'mutate([f], os.getpid())', 'mutate({f: 0}, os.getpid())', 'mutate(holder, os.getpid())'):
            with self.subTest(mutation=mutation):
                graph = self.graph({'entry': 'import os, io\nclass Holder:\n    pass\nf = io.BytesIO()\n'
                                    'holder = Holder()\nholder.stream = f\n' + mutation + '\nraw = f.read()\n'})
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), self.nodes(graph, 'symbol', 'raw')))
                self.assertTrue(any(r['reason'].startswith(('stream_attribute_write_summary_required', 'stream_escape_effects_summary_required'))
                                    for r in graph['unclassified']))

    def test_stream_bound_read_alias_retains_its_stream_state(self):
        graph = self.graph({'entry': 'import io\nf = io.StringIO("first")\nread = f.read\n'
                            'f = io.StringIO("second")\nraw = read()\n'})
        call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'read()'))
        states = {r['identity']:r for r in graph['stream_state_inventory']}
        targets = [t for t in call['targets'] if t[0] == 'stream_method']
        self.assertTrue(targets)
        self.assertTrue(all(states[t[2]]['factory'] == 'io.StringIO' for t in targets))
        self.assertTrue(all(any(r['node'] == call['node'] and states[t[2]]['state_node'] in r['inputs']
                                for r in graph['stream_contract_inventory']) for t in targets))

    def test_stream_buffer_and_detach_preserve_shared_backing_provenance(self):
        graph = self.graph({'entry': 'import io, os\nbase = io.BytesIO()\nf = io.TextIOWrapper(base)\n'
                            'f.buffer.write(os.urandom(4))\nraw = f.read()\nother = f.detach()\nother.read()\n'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.urandom(4)'), self.nodes(graph, 'symbol', 'raw')))
        factories = {r['factory'] for r in graph['stream_state_inventory']}
        self.assertTrue({'io.BytesIO', 'io.TextIOWrapper', 'stream.buffer', 'stream.detach'} <= factories)
        self.assertTrue(any(r['reason'] == 'stream_backing_dispatch_summary_required:buffer' for r in graph['unclassified']))

    def test_stream_mutated_buffer_alias_is_an_explicit_unresolved_consequence(self):
        graph = self.graph({'entry': 'f = open("/x", "rb")\ncount = f.readinto(buffer)\n'})
        row = next(r for r in graph['stream_contract_inventory'] if r['api'] == 'stream.readinto')
        self.assertIn('buffer_mutation', row['effects'])
        self.assertTrue(self.reachable(graph, {row['effects']['external_read']}, {row['effects']['buffer_mutation']}))
        self.assertTrue(any(r['reason'] == 'stream_mutated_buffer_alias_summary_required' for r in graph['unclassified']))

    def test_stream_stdio_rebinding_and_nested_buffer_remain_conditional(self):
        graph = self.graph({'entry': 'import sys\nf = sys.stdout\nsys.stdout = unknown\n'
                            'f.buffer.write(b"payload")\nraw = sys.stdin.read()\n'})
        factories = {r['factory'] for r in graph['stream_state_inventory']}
        self.assertTrue({'sys.stdout', 'sys.stdin', 'stream.buffer'} <= factories)
        self.assertTrue(any(r['reason'] == 'external_attribute_write_summary_required:stdout' for r in graph['unclassified']))
        self.assertTrue(all(r['classification'] == 'conditional_possible_branch' for r in graph['stream_contract_inventory']))

    def test_stream_writelines_items_reach_write_without_returning_callable_items(self):
        graph = self.graph({'entry': 'import os\ndef forbidden():\n    pass\nf = open("/x", "wb")\n'
                            'result = f.writelines([os.urandom(2), forbidden])\nresult()\n'})
        row = next(r for r in graph['stream_contract_inventory'] if r['api'] == 'stream.writelines')
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.urandom(2)'), {row['effects']['external_write']}))
        call = next(r for r in graph['calls'] if r['node'] in self.nodes(graph, 'Call', 'result()'))
        self.assertFalse(any('::forbidden@' in t[1] for t in call['targets']))
        self.assertTrue(any(r['reason'] == 'stream_writelines_iteration_summary_required' for r in graph['unclassified']))

    def test_stream_direct_enter_and_close_keep_lifecycle_open(self):
        graph = self.graph({'entry': 'import io\nf = io.BytesIO(b"a")\ng = f.__enter__()\n'
                            'f.close()\nraw = g.read()\nf.__exit__(None, None, None)\n'})
        calls = {r['api'] for r in graph['stream_contract_inventory']}
        self.assertTrue({'stream.__enter__', 'stream.close', 'stream.read', 'stream.__exit__'} <= calls)
        self.assertTrue(any(r['reason'] == 'stream_lifecycle_summary_required' for r in graph['unclassified']))
        read = next(r for r in graph['stream_contract_inventory'] if r['api'] == 'stream.read')
        self.assertFalse(any(r['node'] == read['node'] for r in graph['primitive_effects']))

    def test_path_receiver_survives_constructor_resolution_parent_and_join(self):
        graph = self.graph({'entry': 'import os\nfrom pathlib import Path\n'
                            'root = Path(os.getenv("ROOT")).resolve().parent\n'
                            'raw = (root / "record.json").read_bytes()\n'})
        apis = {row['api'] for row in graph['path_contract_inventory']}
        self.assertTrue({'pathlib.Path', 'pathlib.Path.resolve', 'pathlib.Path.parent',
                         'pathlib.Path.__truediv__', 'pathlib.Path.read_bytes'} <= apis)
        read = next(row for row in graph['path_contract_inventory'] if row['api'] == 'pathlib.Path.read_bytes')
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', "os.getenv('ROOT')"), {read['node']}))
        self.assertIn('filesystem_read', read['effects'])
        self.assertTrue(self.reachable(graph, {read['effects']['filesystem_read']}, self.nodes(graph, 'symbol', 'raw')))
        self.assertTrue(all(row['classification'] == 'conditional_possible_branch' for row in graph['path_contract_inventory']))
        self.assertFalse(graph['source_audit_complete'])

    def test_path_write_exposes_destination_and_payload_without_callable_alias(self):
        graph = self.graph({'entry': 'import os\nfrom pathlib import Path\n'
                            'def forbidden():\n    pass\n'
                            'p = Path(os.getenv("DEST"))\ncount = p.write_bytes(forbidden)\ncount()\n'})
        row = next(row for row in graph['path_contract_inventory'] if row['api'] == 'pathlib.Path.write_bytes')
        sink = {row['effects']['filesystem_write']}
        for starts in (self.nodes(graph, 'Call', "os.getenv('DEST')"), self.nodes(graph, 'name_read', 'forbidden')):
            self.assertTrue(self.reachable(graph, starts, sink))
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'count()'))
        self.assertFalse(any('::forbidden@' in target[1] for target in call['targets']))
        self.assertTrue(any(row['reason'] == 'path_api_effects_summary_required:pathlib.Path.write_bytes'
                            for row in graph['unclassified']))

    def test_path_iterators_keep_filesystem_and_lifecycle_inputs(self):
        for expression in ('root.iterdir()', 'root.glob("*.json")', 'root.rglob("*.json")'):
            with self.subTest(expression=expression):
                graph = self.graph({'entry': 'from pathlib import Path\nroot = Path("/data")\n'
                                    'for child in ' + expression + ':\n    raw = child.read_bytes()\n'})
                iterator = next(row for row in graph['path_contract_inventory'] if row['result_kind'] == 'path_iterator')
                read = next(row for row in graph['path_contract_inventory'] if row['api'] == 'pathlib.Path.read_bytes')
                self.assertTrue(self.reachable(graph, {iterator['effects']['filesystem_read']}, {read['node']}))
                self.assertTrue(any(row['reason'] == 'path_iteration_lifecycle_summary_required' for row in graph['unclassified']))
                self.assertTrue(any(row['reason'] == 'iteration_receiver_summary_required' for row in graph['unclassified']))

    def test_path_parents_integer_index_and_slice_do_not_share_result_kind(self):
        graph = self.graph({'entry': 'from pathlib import Path\np = Path("/a/b/c")\n'
                            'a = p.parents[1].read_bytes()\nb = p.parents[:1].read_bytes()\n'
                            'c = p.parents[unknown].read_bytes()\n'})
        reads = [row for row in graph['path_contract_inventory'] if row['api'] == 'pathlib.Path.read_bytes']
        self.assertEqual(len(reads), 1)
        self.assertIn(reads[0]['node'], self.nodes(graph, 'Call', 'p.parents[1].read_bytes()'))
        self.assertTrue(any(row['reason'] == 'path_parent_selector_summary_required' for row in graph['unclassified']))

    def test_path_method_alias_keeps_its_original_receiver(self):
        graph = self.graph({'entry': 'from pathlib import Path\n'
                            'p = Path("/first")\nread = p.read_bytes\np = Path("/second")\nraw = read()\n'})
        target = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'read()'))
        method = next(v for v in target['targets'] if v[:2] == ['path_method', 'pathlib.Path.read_bytes'])
        receiver = int(method[2])
        self.assertIn(receiver, self.nodes(graph, 'name_read', 'p'))
        self.assertEqual(graph['nodes'][receiver]['line'], 3)
        self.assertTrue(any(row['node'] == target['node'] and receiver in row['inputs']
                            for row in graph['path_contract_inventory']))
        # Flow-insensitive aliases do not establish which assignment executed.
        self.assertFalse(any(row['node'] == target['node'] for row in graph['primitive_effects']))

    def test_path_mixed_receivers_and_shadowed_factory_remain_conditional(self):
        graph = self.graph({'entry': 'from pathlib import Path\n'
                            'class Other:\n    def read_bytes(self):\n        return unknown\n'
                            'p = Path("/x")\np = Other()\np = unresolved\nraw = p.read_bytes()\n'})
        row = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'p.read_bytes()'))
        self.assertTrue(any(target[0] == 'path_method' for target in row['targets']))
        self.assertTrue(any(target[0] == 'bound' and '.read_bytes@' in target[1] for target in row['targets']))
        self.assertFalse(any(effect['node'] == row['node'] for effect in graph['primitive_effects']))
        self.assertTrue(any(item['reason'] == 'attribute_receiver_summary_required:read_bytes' for item in graph['unclassified']))
        shadowed = self.graph({'entry': 'class Path:\n    def read_bytes(self):\n        return unknown\nPath().read_bytes()\n'})
        self.assertEqual(shadowed['path_contract_inventory'], [])

    def test_path_attribute_mutation_remains_in_later_read_provenance(self):
        graph = self.graph({'entry': 'import os\nfrom pathlib import Path\np = Path("/x")\n'
                            'p._raw_paths = os.getpid()\nraw = p.read_bytes()\nsecret = p._private()\n'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), self.nodes(graph, 'symbol', 'raw')))
        reasons = {row['reason'] for row in graph['unclassified']}
        self.assertIn('path_attribute_write_summary_required:_raw_paths', reasons)
        self.assertIn('path_attribute_summary_required:_private', reasons)

    def test_path_unknown_call_escape_preserves_mutator_inputs(self):
        for argument in ('p', '[p]', '{"path": p}', 'holder'):
            with self.subTest(argument=argument):
                graph = self.graph({'entry': 'import os\nfrom pathlib import Path\n'
                                    'class Holder:\n    pass\np = Path("/x")\nholder = Holder()\nholder.path = p\n'
                                    'mutate(' + argument + ', os.getpid())\nraw = p.read_bytes()\n'})
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), self.nodes(graph, 'symbol', 'raw')))
                self.assertTrue(any(row['reason'] == 'path_external_mutation_summary_required' for row in graph['unclassified']))

    def test_path_platform_factories_and_open_keep_both_access_directions(self):
        graph = self.graph({'entry': 'from pathlib import Path, PosixPath\n'
                            'p = Path.cwd().parent\nq = PosixPath.home().expanduser()\n'
                            'handle = p.open(mode)\nname = q.name\n'})
        for api in ('pathlib.Path.cwd', 'pathlib.PosixPath.home', 'pathlib.Path.expanduser'):
            row = next(row for row in graph['path_contract_inventory'] if row['api'] == api)
            self.assertIn('platform_input', row['effects'])
        row = next(row for row in graph['path_contract_inventory'] if row['api'] == 'pathlib.Path.open')
        self.assertTrue({'filesystem_read', 'filesystem_write'} <= set(row['effects']))
        self.assertTrue(any(row['api'] == 'pathlib.Path.name' for row in graph['path_contract_inventory']))

    def test_path_division_never_closes_reflected_dispatch_or_result_type(self):
        graph = self.graph({'entry': 'from pathlib import Path\n'
                            'class Operand:\n    def __rtruediv__(self, other):\n        return unknown\n'
                            'a = Path("/x") / Operand()\nb = unknown / Path("/y")\n'
                            'a.read_bytes()\nb.read_bytes()\n'})
        divisions = {row['node'] for row in graph['path_contract_inventory'] if row['api'].endswith(('__truediv__', '__rtruediv__'))}
        self.assertEqual(len(divisions), 2)
        self.assertFalse(any(row['node'] in divisions for row in graph['primitive_effects']))
        self.assertTrue(all(any(row['node'] == node and row['reason'] == 'path_operand_dispatch_summary_required'
                                for row in graph['unclassified']) for node in divisions))

    def test_path_rename_keeps_unknown_target_and_callback_result_alternatives(self):
        graph = self.graph({'entry': 'from pathlib import Path\np = Path("/x")\n'
                            'result = p.rename(unknown)\nresult.read_bytes()\n'})
        row = next(row for row in graph['path_contract_inventory'] if row['api'] == 'pathlib.Path.rename')
        self.assertIn('filesystem_write', row['effects'])
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'symbol', 'unknown'), {row['effects']['filesystem_write']}))
        self.assertFalse(any(effect['node'] == row['node'] for effect in graph['primitive_effects']))
        self.assertIn('receiver_and_operand_dispatch_classified', row['preconditions'])
        self.assertTrue(any(item['reason'] == 'attribute_receiver_summary_required:read_bytes' for item in graph['unclassified']))

    def test_hash_updates_reach_digest_through_bound_method_alias(self):
        graph = self.graph({'entry': 'import os, hashlib\nh = hashlib.sha256(b"start")\n'
                            'feed = h.update\nfeed(os.urandom(8))\nowner = h.hexdigest()\n'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.urandom(8)'),
                                       self.nodes(graph, 'symbol', 'owner')))
        calls = [row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'feed(os.urandom(8))')]
        self.assertEqual(calls[0]['targets'][0][0:2], ['hash_method', 'update'])
        self.assertTrue(any(row['reason'] == 'hash_method_summary_required:update' for row in graph['unclassified']))
        self.assertEqual(len(graph['hash_state_inventory']), 1)

    def test_hash_byte_effects_and_digest_types_keep_binding_precondition(self):
        graph = self.graph({'entry': 'import hashlib\nh = hashlib.sha256(b"a", usedforsecurity=True)\n'
                            'h.update(b"b")\nraw = h.digest()\ntext = h.hexdigest()\nlength = len(text)\n'})
        effects = {row['operation']: row for row in graph['primitive_effects']}
        for name in ('hashlib.sha256', 'hash.update', 'hash.digest', 'hash.hexdigest'):
            self.assertEqual(effects[name]['preconditions'], ['authentic_stdlib_binding:hashlib'])
        for name, output in (('hash.update', ['NoneType']), ('hash.digest', ['bytes']), ('hash.hexdigest', ['str'])):
            self.assertEqual(effects[name]['output_types'], output)
        self.assertIn('builtins.len', effects)
        self.assertTrue(any(row['reason'] == 'stdlib_binding_summary_required:hashlib' for row in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])

    def test_hash_copy_has_separate_state_and_retains_prefix_provenance(self):
        graph = self.graph({'entry': 'import os, hashlib\nprefix = os.urandom(2)\n'
                            'original = hashlib.sha256(prefix)\ncopy = original.copy()\n'
                            'copy.update(os.urandom(3))\na = original.hexdigest()\nb = copy.hexdigest()\n'})
        self.assertEqual(len(graph['hash_state_inventory']), 2)
        prefix = self.nodes(graph, 'Call', 'os.urandom(2)')
        added = self.nodes(graph, 'Call', 'os.urandom(3)')
        self.assertTrue(self.reachable(graph, prefix, self.nodes(graph, 'symbol', 'a')))
        self.assertTrue(self.reachable(graph, prefix, self.nodes(graph, 'symbol', 'b')))
        self.assertFalse(self.reachable(graph, added, self.nodes(graph, 'symbol', 'a')))
        self.assertTrue(self.reachable(graph, added, self.nodes(graph, 'symbol', 'b')))
        self.assertTrue(all(row['snapshot_model'] == 'flow_insensitive_possible_inputs' for row in graph['hash_state_inventory']))

    def test_hash_inputs_never_turn_digest_bytes_or_text_into_callable_aliases(self):
        graph = self.graph({'entry': 'import hashlib\ndef forbidden():\n    pass\n'
                            'h = hashlib.sha256(forbidden)\nselected = h.hexdigest()\nselected()\n'})
        selected = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'selected()'))
        self.assertFalse(any('::forbidden@' in target[1] for target in selected['targets']))
        self.assertTrue(any(row['reason'] == 'external_api_summary_required:hashlib.sha256' for row in graph['unclassified']))

    def test_hash_unknown_receivers_and_mixed_factory_aliases_cannot_close_effects(self):
        examples = ('import hashlib\nmake = hashlib.sha256\nmake = unknown\nh = make()\nh.hexdigest()\n',
                    'import hashlib\nh = hashlib.sha256()\nh = unknown\nh.hexdigest()\n',
                    'class Fake:\n    def hexdigest(self):\n        return unknown\nFake().hexdigest()\n')
        for source in examples:
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                self.assertFalse(any(row['operation'] == 'hash.hexdigest' for row in graph['primitive_effects']))

    def test_hash_arity_buffers_and_policy_flag_hooks_stay_unproved(self):
        import ast
        for expression in ('hashlib.sha256(unknown)', 'hashlib.sha256(b"a", b"b")',
                           'hashlib.sha256(*unknown)', 'hashlib.sha256(b"a", usedforsecurity=unknown)',
                           'h.update(unknown)', 'h.update(data=b"a")', 'h.digest(1)', 'h.copy(extra=True)'):
            with self.subTest(expression=expression):
                graph = self.graph({'entry': 'import hashlib\nh = hashlib.sha256()\nresult = ' + expression + '\n'})
                syntax = ast.unparse(ast.parse(expression, mode='eval').body)
                nodes = self.nodes(graph, 'Call', syntax)
                self.assertFalse(any(row['node'] in nodes for row in graph['primitive_effects']))
                self.assertTrue(any(row['node'] in nodes for row in graph['unclassified']))

    def test_hash_escape_retains_unknown_mutator_arguments_and_state_obligation(self):
        for argument in ('h', '[h]', '{"hash": h}'):
            with self.subTest(argument=argument):
                graph = self.graph({'entry': 'import os, hashlib\nh = hashlib.sha256(b"start")\n'
                                    'mutate(' + argument + ', os.urandom(4))\nowner = h.hexdigest()\n'})
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.urandom(4)'), self.nodes(graph, 'symbol', 'owner')))
                self.assertTrue(any(row['reason'] == 'hash_external_mutation_summary_required' for row in graph['unclassified']))

    def test_hash_local_function_transfer_and_known_algorithms_remain_distinct(self):
        graph = self.graph({'entry': 'from hashlib import sha1 as one\nfrom hashlib import sha256 as two\n'
                            'def feed(h, value):\n    h.update(value)\n'
                            'first = one(b"a")\nsecond = two(b"b")\nfeed(first, unknown)\n'
                            'a = first.hexdigest()\nb = second.hexdigest()\n'})
        self.assertEqual({row['algorithm'] for row in graph['hash_state_inventory']}, {'sha1', 'sha256'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'symbol', 'unknown'), self.nodes(graph, 'symbol', 'a')))
        self.assertFalse(self.reachable(graph, self.nodes(graph, 'symbol', 'unknown'), self.nodes(graph, 'symbol', 'b')))
        self.assertFalse(any(row['operation'] == 'hash.update' for row in graph['primitive_effects']))

    def test_hash_attribute_writes_and_unsupported_factory_remain_open(self):
        graph = self.graph({'entry': 'import hashlib\nh = hashlib.sha256()\nh.update = unknown\n'
                            'hashlib.sha256 = unknown\nother = hashlib.new("sha256")\nother.hexdigest()\n'})
        reasons = {row['reason'] for row in graph['unclassified']}
        self.assertIn('hash_attribute_summary_required:update', reasons)
        self.assertIn('external_attribute_write_summary_required:sha256', reasons)
        self.assertIn('stdlib_binding_summary_required:hashlib', reasons)
        self.assertIn('external_api_summary_required:hashlib.new', reasons)
        self.assertFalse(any(row['node'] in self.nodes(graph, 'Call', 'other.hexdigest()') for row in graph['primitive_effects']))
        self.assertFalse(graph['source_audit_complete'])

    def test_return_shape_requires_closed_builtin_identity_and_never_makes_a_callable_alias(self):
        for source in ('fn = len\nfn = unknown\nvalue = fn([])\n',
                       'def len(value):\n    return value\nvalue = len([])\n',
                       'def choose(fn):\n    return fn([])\nchoose(len)\n'):
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                self.assertFalse(graph['builtin_return_facts'])
        graph = self.graph({'entry': 'from builtins import len as size\nvalue = size(unknown)\nvalue()\n'})
        fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'builtins.len')
        self.assertIsNotNone(fact['unresolved_effect_obligation'])
        called = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'value()'))
        self.assertNotIn(['external', 'builtins.len', ''], called['targets'])
        self.assertTrue(any(row['node'] == called['node'] and row['reason'].startswith('callable_identity_unclassified:')
                            for row in graph['unclassified']))

    def test_expanded_or_invalid_arguments_cannot_turn_return_shape_into_acceptance(self):
        for call in ('len(*unknown)', 'len(**unknown)', 'len(value=unknown)', 'len()', 'len(1, 2)'):
            with self.subTest(call=call):
                graph = self.graph({'entry': 'value = ' + call + '\nresult = value + 1\n'})
                fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'builtins.len')
                self.assertEqual(fact['output_types'], ['int'])
                self.assertEqual(fact['unresolved_effect_obligation'], 'external_api_summary_required:builtins.len')
                self.assertFalse(any(row['operation'] == 'builtins.len' for row in graph['primitive_effects']))
                self.assertTrue(graph['unclassified'])

    def test_range_conversion_effect_stays_open_while_its_actual_item_type_is_known(self):
        graph = self.graph({'entry': 'def derive(unknown):\n'
                            '    for item in range(unknown):\n        value = item + 1\n'
                            '    return value\n'})
        fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'builtins.range')
        self.assertEqual(fact['unresolved_effect_obligation'], 'external_api_summary_required:builtins.range')
        self.assertTrue(any(row['operation'] == 'immutable_sequence_iteration' and row['output_types'] == ['int']
                            for row in graph['primitive_effects']))
        self.assertFalse(any(row['reason'] == 'iteration_receiver_summary_required' for row in graph['unclassified']))
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'symbol', 'unknown', 'derive'),
                                       self.nodes(graph, 'symbol', 'value', 'derive')))

    def test_owned_cpu_callbacks_confirm_return_types_without_claiming_purity(self):
        events = []
        class Value:
            def __len__(self):
                events.append('length')
                return 3
            def __bool__(self):
                events.append('truth')
                return True
            def __hash__(self):
                events.append('hash')
                return 7
            def __index__(self):
                events.append('index')
                return 3
            def __getattr__(self, name):
                events.append('attribute')
                return 1
            def __iter__(self):
                events.append('iterate')
                return iter([self])
        class Meta(type):
            def __instancecheck__(cls, value):
                events.append('instance')
                return Value()
            def __subclasscheck__(cls, value):
                events.append('subclass')
                return Value()
        class Checked(metaclass=Meta):
            pass
        value = Value()
        examples = [('len(unknown)', len(value), int), ('bool(unknown)', bool(value), bool),
                    ('hash(unknown)', hash(value), int), ('id(unknown)', id(value), int),
                    ('range(unknown)', range(value), range), ('chr(unknown)', chr(value), str),
                    ('hex(unknown)', hex(value), str), ('oct(unknown)', oct(value), str),
                    ('ord(unknown)', ord('a'), int), ('callable(unknown)', callable(value), bool),
                    ('hasattr(unknown, "owner")', hasattr(value, 'owner'), bool),
                    ('isinstance(unknown, check)', isinstance(value, Checked), bool),
                    ('issubclass(unknown, check)', issubclass(Value, Checked), bool),
                    ('all(unknown)', all(value), bool), ('any(unknown)', any(value), bool)]
        for call, actual, expected in examples:
            with self.subTest(call=call):
                self.assertIs(type(actual), expected)
                graph = self.graph({'entry': 'def check_result(unknown, check):\n    return ' + call + '\n'})
                fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'builtins.' + call.split('(')[0])
                self.assertEqual(fact['output_types'], [expected.__name__])
                self.assertIsNotNone(fact['unresolved_effect_obligation'])
        self.assertEqual(set(events), {'length', 'truth', 'hash', 'index', 'attribute', 'instance', 'subclass', 'iterate'})

    def test_subclass_and_arbitrary_conversion_returns_do_not_get_exact_builtin_facts(self):
        class Text(str):
            pass
        class Value:
            def __str__(self):
                return Text('owned')
            def __repr__(self):
                return Text('owned')
            def __abs__(self):
                return self
        value = Value()
        self.assertIs(type(str(value)), Text)
        self.assertIs(type(repr(value)), Text)
        self.assertIs(type(ascii(value)), Text)
        self.assertIs(abs(value), value)
        for expression in ('str(unknown)', 'repr(unknown)', 'ascii(unknown)', 'abs(unknown)'):
            with self.subTest(expression=expression):
                graph = self.graph({'entry': 'def derive(unknown):\n    value = ' + expression + '\n    return value + 1\n'})
                self.assertFalse(graph['builtin_return_facts'])
                nodes = self.nodes(graph, 'BinOp', 'value + 1')
                self.assertFalse(any(row['node'] in nodes for row in graph['primitive_effects']))

    def test_builtin_protocol_reads_trace_platform_inputs_through_local_methods(self):
        for builtin, method in (('len', '__len__'), ('hash', '__hash__'), ('bool', '__bool__'),
                                ('range', '__index__'), ('chr', '__index__'), ('hex', '__index__'), ('oct', '__index__')):
            with self.subTest(builtin=builtin):
                graph = self.graph({'entry': 'import os\nclass Value:\n'
                                    '    def ' + method + '(self):\n        return os.getpid()\n'
                                    'result = ' + builtin + '(Value())\n'})
                callbacks = [row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'builtins.' + builtin]
                self.assertEqual(len(callbacks), 1)
                self.assertEqual(callbacks[0]['method'], method)
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                               self.nodes(graph, 'symbol', 'result')))
                self.assertTrue(any(row['node'] == callbacks[0]['builtin_node']
                                    and row['reason'] == 'external_api_summary_required:builtins.' + builtin
                                    for row in graph['unclassified']))
                self.assertFalse(graph['source_audit_complete'])

    def test_special_method_lookup_bypasses_instance_field_and_controls_its_side_effect(self):
        graph = self.graph({'entry': 'import os, time\nowner = "B"\n'
                            'class Value:\n'
                            '    def __init__(self):\n        self.__len__ = time.monotonic\n'
                            '    def __len__(self):\n        global owner\n        owner = "A"\n        return 1\n'
                            'if os.getpid():\n    result = len(Value())\n'})
        edge = next(row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'builtins.len')
        call = next(row for row in graph['calls'] if row['node'] == edge['callback_node'])
        self.assertEqual(len(call['targets']), 1)
        self.assertEqual(call['targets'][0][0], 'bound')
        self.assertIn('Value.__len__@', call['targets'][0][1])
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                       self.nodes(graph, 'symbol', 'owner', '<module>')))

    def test_bool_slot_precedence_and_length_fallback_are_distinct(self):
        for boolean_slot, expected in (
                ('    def __bool__(self):\n        return True\n', '__bool__'),
                ('', '__len__'), ('    __bool__ = None\n', None)):
            with self.subTest(boolean_slot=boolean_slot):
                graph = self.graph({'entry': 'class Value:\n' + boolean_slot +
                                    '    def __len__(self):\n        return 1\nresult = bool(Value())\n'})
                edges = [row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'builtins.bool']
                self.assertEqual([row['method'] for row in edges], [] if expected is None else [expected])
                if expected is None:
                    self.assertTrue(any(row['reason'] == 'special_method_binding_summary_required:builtins.bool.__bool__'
                                        for row in graph['unclassified']))

    def test_special_static_methods_bind_without_self_and_descriptors_stay_open(self):
        graph = self.graph({'entry': 'class Value:\n'
                            '    @staticmethod\n    def __len__():\n        return 1\nresult = len(Value())\n'})
        edge = next(row for row in graph['builtin_protocol_edges'] if row['builtin'] == 'builtins.len')
        call = next(row for row in graph['calls'] if row['node'] == edge['callback_node'])
        self.assertEqual(call['targets'][0][0], 'function')
        self.assertFalse(any(row['node'] == call['node'] and 'binding_mismatch' in row['reason'] for row in graph['unclassified']))
        for decorator in ('property', 'classmethod'):
            with self.subTest(decorator=decorator):
                graph = self.graph({'entry': 'class Value:\n'
                                    '    @' + decorator + '\n    def __len__(self):\n        return 1\nresult = len(Value())\n'})
                self.assertFalse(graph['builtin_protocol_edges'])
                self.assertTrue(any(row['reason'] == 'special_method_descriptor_summary_required:builtins.len.__len__'
                                    for row in graph['unclassified']))

    def test_invalid_and_unknown_protocol_arguments_cannot_invent_local_callbacks(self):
        for expression in ('len()', 'len(value, value)', 'len(value=value)', 'len(*unknown)'):
            with self.subTest(expression=expression):
                graph = self.graph({'entry': 'class Value:\n'
                                    '    def __len__(self):\n        return 1\n'
                                    'value = Value()\nresult = ' + expression + '\n'})
                self.assertFalse(graph['builtin_protocol_edges'])
                self.assertTrue(any(row['reason'] == 'external_api_summary_required:builtins.len' for row in graph['unclassified']))

    def test_special_method_return_cannot_alias_the_converted_builtin_result(self):
        graph = self.graph({'entry': 'import os\nclass Value:\n'
                            '    def __len__(self):\n        return os.getpid\n'
                            'result = len(Value())\nresult()\n'})
        self.assertTrue(graph['builtin_protocol_edges'])
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'result()'))
        self.assertNotIn(['external', 'os.getpid', ''], call['targets'])
        self.assertTrue(any(row['node'] == call['node'] and row['reason'].startswith('callable_identity_unclassified:')
                            for row in graph['unclassified']))

    def test_platform_control_of_class_or_special_slot_reaches_builtin_result(self):
        sources = (
            'import os\nclass A:\n    def __len__(self):\n        return 1\n'
            'class B:\n    def __len__(self):\n        return 2\n'
            'factory = A if os.getpid() else B\nresult = len(factory())\n',
            'import os\ndef first(self):\n    return 1\ndef second(self):\n    return 2\n'
            'class Value:\n    if os.getpid():\n        __len__ = first\n'
            '    else:\n        __len__ = second\nresult = len(Value())\n')
        for source in sources:
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                self.assertEqual(len(graph['builtin_protocol_edges']), 2)
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                               self.nodes(graph, 'symbol', 'result')))
                self.assertTrue(all(row['binding'] == 'possible_local_slot' for row in graph['builtin_protocol_edges']))

    def test_shadowed_descriptor_spelling_cannot_hide_decorator_code(self):
        for spelling in ('staticmethod', 'property', 'classmethod'):
            with self.subTest(spelling=spelling):
                graph = self.graph({'entry': 'import os\ndef ' + spelling + '(fn):\n'
                                    '    def wrapped(self):\n        return os.getpid()\n'
                                    '    return wrapped\nclass Value:\n'
                                    '    @' + spelling + '\n    def __len__():\n        return 1\n'
                                    'result = len(Value())\n'})
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                               self.nodes(graph, 'symbol', 'result')))
                self.assertTrue(any('wrapped@' in row['target_definition'] for row in graph['builtin_protocol_edges']))

    def test_composed_or_standalone_descriptors_need_their_own_binding_contract(self):
        for source in ('def wrap(fn):\n    return fn\nclass Value:\n'
                       '    @staticmethod\n    @wrap\n    def __len__():\n        return 1\n',
                       '@staticmethod\ndef value():\n    return 1\n'):
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                self.assertTrue(any(row['reason'] == 'descriptor_composition_summary_required'
                                    for row in graph['unclassified']))

    def test_type_inspection_does_not_claim_builtin_metaclass_or_callable_alias(self):
        graph = self.graph({'entry': 'def inspect(unknown):\n'
                            '    cls = type(unknown)\n'
                            '    if cls:\n        cls()\n'
                            '    return cls is int\n'})
        self.assertTrue(any(row['operation'] == 'builtins.type' and row['output_types'] == ['runtime_class']
                            for row in graph['primitive_effects']))
        self.assertTrue(any(row['reason'] == 'truth_value_protocol_summary_required' for row in graph['unclassified']))
        called = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'cls()'))
        self.assertNotIn(['external', 'builtins.int', ''], called['targets'])

    def test_immutable_sequence_index_slice_and_iteration_keep_input_edges(self):
        graph = self.graph({'entry': 'text = "abc"\nletter = text[1]\npart = text[1:]\n'
                            'byte = b"ABC"[0]\n'
                            'for item in b"ABC":\n    value = item + 1\n'
                            'for index in range(3):\n    value2 = index + 1\n'})
        expected = {"text[1]": ['str'], 'text[1:]': ['str'], "b'ABC'[0]": ['int']}
        for label, output in expected.items():
            node = self.nodes(graph, 'Subscript', label)
            effect = next(row for row in graph['primitive_effects'] if row['node'] in node)
            self.assertEqual(effect['output_types'], output)
        self.assertEqual(sum(row['operation'] == 'immutable_sequence_iteration' for row in graph['primitive_effects']), 2)
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Constant', "'abc'"), self.nodes(graph, 'symbol', 'part')))
        self.assertFalse(any(row['reason'] == 'iteration_receiver_summary_required' for row in graph['unclassified']))

    def test_custom_index_and_unknown_slice_bound_remain_unclassified(self):
        for expression in ('text[unknown]', 'text[unknown:]', 'text[::unknown]', 'unknown[0]'):
            with self.subTest(expression=expression):
                graph = self.graph({'entry': 'text = "abc"\nvalue = ' + expression + '\n'})
                self.assertTrue(any(row['reason'] == 'subscript_receiver_summary_required' for row in graph['unclassified']))
                self.assertFalse(any(row['operation'] == 'immutable_sequence_subscript' for row in graph['primitive_effects']))

    def test_implicit_truth_and_augmented_operations_retain_custom_protocol_obligations(self):
        graph = self.graph({'entry': 'def choose(unknown):\n'
                            '    if unknown:\n        value = 1\n'
                            '    while unknown:\n        break\n'
                            '    assert unknown\n'
                            '    value = unknown and 1\n'
                            '    value += unknown\n'
                            '    return not unknown\n'})
        reasons = {row['reason'] for row in graph['unclassified']}
        self.assertIn('truth_value_protocol_summary_required', reasons)
        self.assertIn('operand_protocol_summary_required:AugAssign', reasons)
        self.assertIn('operand_protocol_summary_required:UnaryOp', reasons)
        self.assertFalse(any(row['operation'] == 'truth_test' for row in graph['primitive_effects']))
        exact = self.graph({'entry': 'assert "a"\nif []:\n    pass\nvalue = 1 and 2\n'})
        self.assertFalse(any(row['reason'] == 'truth_value_protocol_summary_required' for row in exact['unclassified']))

    def test_chained_comparison_control_reaches_later_operand_side_effect(self):
        graph = self.graph({'entry': 'import os\nowner = "B"\n'
                            'def write():\n    global owner\n    owner = "A"\n    return 1\n'
                            'result = os.getpid() is None is write()\n'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                       self.nodes(graph, 'symbol', 'owner', '<module>')))
        self.assertTrue(any(node['kind'] == 'comparison_step' for node in graph['nodes']))
        self.assertFalse(any(row['reason'] == 'operand_protocol_summary_required:Compare' for row in graph['unclassified']))

    def test_element_comparison_and_percent_formatting_are_not_scalar_summaries(self):
        for expression in ('[1] == [1]', '{1} == {1}', '"%s" % unknown', 'unknown in [1]', 'f"{unknown}"'):
            with self.subTest(expression=expression):
                graph = self.graph({'entry': 'value = ' + expression + '\n'})
                self.assertTrue(any(row['reason'].startswith('operand_protocol_summary_required:') for row in graph['unclassified']))

    def test_input_follows_import_alias_return_and_parameter(self):
        graph = self.graph({'helper': 'def identity(value):\n    return value\n',
                            'entry': 'import os as platform\nfrom helper import identity as relay\n'
                                     'def owner():\n    return relay(platform.getpid())\n'})
        source = self.nodes(graph, 'Call', 'platform.getpid()')
        target = self.nodes(graph, 'return_slot', function='owner')
        self.assertTrue(source and target)
        self.assertTrue(self.reachable(graph, source, target))
        relay = next(call for call in graph['calls'] if call['node'] in self.nodes(graph, 'Call', 'relay(platform.getpid())'))
        self.assertEqual([target[0] for target in relay['targets']], ['function'])
        self.assertIn('::identity@', relay['targets'][0][1])

    def test_callable_alias_flows_through_return_and_instance_field(self):
        graph = self.graph({'entry': 'import os\n'
                            'def relay(value):\n    return value\n'
                            'class Box:\n'
                            '    def __init__(self, fn):\n        self.fn = fn\n'
                            '    def read(self):\n        return self.fn()\n'
                            'box = Box(relay(os.getpid))\nvalue = box.read()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'self.fn()'))
        self.assertEqual(call['targets'], [['external', 'os.getpid', '']])
        self.assertTrue(self.reachable(graph, {call['node']}, self.nodes(graph, 'symbol', 'value')))

    def test_branch_control_reaches_written_field_and_returned_owner(self):
        graph = self.graph({'entry': 'import os\nclass Box:\n'
                            '    def choose(self):\n'
                            '        if os.getpid():\n            self.owner = "A"\n'
                            '        else:\n            self.owner = "B"\n'
                            '        return self.owner\n'})
        source = self.nodes(graph, 'Call', 'os.getpid()')
        target = self.nodes(graph, 'return_slot', function='Box.choose')
        self.assertTrue(self.reachable(graph, source, target))
        self.assertTrue(any(edge['kind'] == 'control' and not edge['reference'] for edge in graph['edges']))

    def test_conditional_return_controls_later_call_and_store(self):
        graph = self.graph({'entry': 'import os\ndef emit():\n    global published\n    published = "A"\n'
                            'def run():\n    if os.getpid():\n        return\n'
                            '    owner = "A"\n    emit()\n    return owner\n'})
        source = self.nodes(graph, 'Call', 'os.getpid()')
        for kind, label in [('Call', 'emit()'), ('symbol', 'owner'), ('return_slot', None)]:
            self.assertTrue(self.reachable(graph, source, self.nodes(graph, kind, label, 'run')))
        edges = [edge for edge in graph['edges'] if edge['kind'].startswith('statement_completion_')]
        self.assertTrue(edges)
        self.assertTrue(all(not edge['reference'] for edge in edges))
        self.assertTrue(self.reachable(graph, source, self.nodes(graph, 'symbol', 'published')))

    def test_loop_exit_controls_suffix_next_iteration_and_else(self):
        for exit_statement in ('break', 'continue', 'return'):
            with self.subTest(exit_statement=exit_statement):
                graph = self.graph({'entry': 'import os\ndef emit():\n    pass\n'
                                    'def run():\n    for item in (1, 2):\n'
                                    '        emit()\n        if os.getpid():\n            ' + exit_statement + '\n'
                                    '        suffix = "A"\n    else:\n        settled = "B"\n'})
                source = self.nodes(graph, 'Call', 'os.getpid()')
                for kind, label in [('Call', 'emit()'), ('symbol', 'suffix'), ('symbol', 'settled')]:
                    self.assertTrue(self.reachable(graph, source, self.nodes(graph, kind, label)))
                self.assertTrue(any(edge['kind'] == 'loop_continuation_control' and not edge['reference']
                                    for edge in graph['edges']))

    def test_explicit_raise_and_assert_control_following_call(self):
        for statement in ('if os.getpid():\n        raise ValueError()', 'assert os.getpid()'):
            with self.subTest(statement=statement):
                graph = self.graph({'entry': 'import os\ndef emit():\n    pass\n'
                                    'def run():\n    ' + statement + '\n    emit()\n'})
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                               self.nodes(graph, 'Call', 'emit()')))

    def test_nested_function_exit_does_not_control_enclosing_suffix(self):
        graph = self.graph({'entry': 'import os\ndef emit():\n    pass\n'
                            'def run():\n    def inner():\n        if os.getpid():\n            return\n'
                            '    emit()\n'})
        self.assertFalse(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                        self.nodes(graph, 'Call', 'emit()')))

    def test_exit_control_does_not_cross_independent_branch_sequences(self):
        graph = self.graph({'entry': 'import os\ndef emit():\n    pass\n'
                            'def run(flag):\n    if flag:\n        if os.getpid():\n            return\n'
                            '    else:\n        emit()\n    after = "A"\n'})
        source = self.nodes(graph, 'Call', 'os.getpid()')
        self.assertFalse(self.reachable(graph, source, self.nodes(graph, 'Call', 'emit()')))
        self.assertTrue(self.reachable(graph, source, self.nodes(graph, 'symbol', 'after')))

    def test_early_exit_does_not_turn_control_into_a_callable_alias(self):
        graph = self.graph({'entry': 'import os\ndef emit():\n    pass\n'
                            'def run():\n    if os.getpid():\n        return\n'
                            '    selected = emit\n    selected()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'selected()'))
        self.assertEqual(len(call['targets']), 1)
        self.assertEqual(call['targets'][0][0], 'function')
        self.assertIn('::emit@', call['targets'][0][1])
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), {call['node']}))

    def test_owned_cpu_exit_choices_change_later_execution(self):
        import inspect
        import textwrap
        def run(choice, mode):
            trace = []
            for index in range(2):
                trace.append(('prefix', index))
                if choice:
                    if mode == 'return':
                        return trace
                    if mode == 'break':
                        break
                    if mode == 'continue':
                        continue
                trace.append(('suffix', index))
            else:
                trace.append(('else', None))
            return trace
        all_steps = [('prefix', 0), ('suffix', 0), ('prefix', 1), ('suffix', 1), ('else', None)]
        for mode, expected in [('return', [('prefix', 0)]), ('break', [('prefix', 0)]),
                               ('continue', [('prefix', 0), ('prefix', 1), ('else', None)])]:
            self.assertEqual(run(False, mode), all_steps)
            self.assertEqual(run(True, mode), expected)
        graph = self.graph({'entry': textwrap.dedent(inspect.getsource(run))})
        choice = self.nodes(graph, 'symbol', 'choice')
        recorded_steps = {node['id'] for node in graph['nodes']
                          if node['kind'] == 'Call' and node['label'].startswith('trace.append(')}
        self.assertEqual(len(recorded_steps), 3)
        self.assertTrue(all(self.reachable(graph, choice, {step}) for step in recorded_steps))

    def test_same_spelled_fields_in_different_classes_do_not_share_aliases(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'class A:\n    def __init__(self):\n        self.fn = os.getpid\n'
                            '    def call(self):\n        return self.fn()\n'
                            'class B:\n    def __init__(self):\n        self.fn = time.monotonic\n'
                            '    def call(self):\n        return self.fn()\n'})
        for function, target in [('A.call', 'os.getpid'), ('B.call', 'time.monotonic')]:
            node = self.nodes(graph, 'Call', 'self.fn()', function)
            call = next(row for row in graph['calls'] if row['node'] in node)
            self.assertEqual(call['targets'], [['external', target, '']])

    def test_container_selected_callable_and_comprehension_are_enumerated(self):
        graph = self.graph({'entry': 'import os\n'
                            'fns = [os.getpid]\nvalues = [fn() for fn in fns]\n'
                            'selected = fns[0]\nresult = selected()\n'})
        calls = [row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()')
                 | self.nodes(graph, 'Call', 'selected()')]
        self.assertEqual(len(calls), 2)
        for call in calls:
            self.assertIn(['external', 'os.getpid', ''], call['targets'])
        self.assertTrue(any('<ListComp@' in row['function'] for row in graph['nodes']))

    def test_external_hash_does_not_turn_its_input_into_a_callable_alias(self):
        graph = self.graph({'entry': 'import os, hashlib\n'
                            'value = hashlib.sha256(os.getpid)\nvalue()\n'})
        node = self.nodes(graph, 'Call', 'value()')
        call = next(row for row in graph['calls'] if row['node'] in node)
        self.assertNotIn(['external', 'os.getpid', ''], call['targets'])
        self.assertTrue(any(row['node'] in node and row['reason'].startswith('callable_identity_unclassified:')
                            for row in graph['unclassified']))

    def test_constant_dictionary_key_and_tuple_unpack_keep_distinct_callables(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'table = {"pid": os.getpid, "clock": time.monotonic}\n'
                            'pid = table["pid"]\nclock, extra = (time.monotonic, os.getpid)\n'
                            'pid()\nclock()\n'})
        for label, expected in [('pid()', 'os.getpid'), ('clock()', 'time.monotonic')]:
            call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
            self.assertEqual(call['targets'], [['external', expected, '']])

    def test_unknown_item_write_is_retained_by_a_later_constant_read(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'def invoke(key):\n'
                            '    table = {"fn": os.getpid}\n'
                            '    table[key] = time.monotonic\n'
                            '    alias = table["fn"]\n'
                            '    return alias()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'alias()'))
        self.assertEqual(call['targets'], [['external', 'os.getpid', ''], ['external', 'time.monotonic', '']])

    def test_write_to_external_module_is_an_explicit_unresolved_boundary(self):
        graph = self.graph({'entry': 'import os\ndef alternate():\n    return 1\nos.getpid = alternate\n'})
        self.assertTrue(any(row['reason'] == 'external_attribute_write_summary_required:getpid'
                            for row in graph['unclassified']))

    def test_unknown_dictionary_key_and_comprehension_item_keep_possible_aliases(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'def invoke(key):\n'
                            '    table = {"fn": time.monotonic, key: os.getpid}\n'
                            '    alias = table["fn"]\n'
                            '    return alias()\n'
                            'values = [fn for fn in [os.getpid]]\n'
                            'from_comp = values[0]\nfrom_comp()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'alias()'))
        self.assertEqual(call['targets'], [['external', 'os.getpid', ''], ['external', 'time.monotonic', '']])
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'from_comp()'))
        self.assertEqual(call['targets'], [['external', 'os.getpid', '']])

    def test_unknown_dynamic_receiver_remains_unresolved(self):
        graph = self.graph({'entry': 'def invoke(unknown):\n    return unknown.callback()\n'})
        node = self.nodes(graph, 'Call', 'unknown.callback()')
        self.assertTrue(any(row['node'] in node and row['reason'] == 'call_target_unresolved'
                            for row in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])

    def test_branch_guard_reaches_helper_side_effect(self):
        graph = self.graph({'entry': 'import os\nowner = "B"\n'
                            'def choose():\n    global owner\n    owner = "A"\n'
                            'if os.getpid():\n    choose()\n'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                       self.nodes(graph, 'symbol', 'owner', '<module>')))
        self.assertTrue(any(edge['kind'] == 'call_control' for edge in graph['edges']))

    def test_nonlocal_alias_and_static_method_binding(self):
        graph = self.graph({'entry': 'import os\n'
                            'def outer():\n'
                            '    alias = os.getpid\n'
                            '    def inner():\n        nonlocal alias\n        return alias()\n'
                            '    return inner()\n'
                            'class Box:\n'
                            '    @staticmethod\n    def read(fn):\n        return fn()\n'
                            'value = Box.read(os.getpid)\n'})
        for label in ('alias()', 'fn()'):
            call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
            self.assertEqual(call['targets'], [['external', 'os.getpid', '']])
        self.assertFalse(any('binding_mismatch' in row['reason'] for row in graph['unclassified']))
        self.assertTrue(all(node['path'] == 'proof_kernel/entry.py' for node in graph['nodes']))

    def test_json_native_decode_result_types_cover_actual_root_values(self):
        import json
        observed = {type(json.loads(raw)).__name__ for raw in (
            'null', 'true', 'false', '0', '1.5', '"text"', '[]', '{}', 'NaN', 'Infinity')}
        graph = self.graph({'entry': 'import json\nvalue=json.loads(raw)\n'})
        fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'json.loads')
        self.assertEqual(set(fact['output_types']), observed)
        self.assertIn('authentic_stdlib_binding:json', fact['preconditions'])
        self.assertIn('native_json_decoder_bindings_stable_during_call', fact['preconditions'])
        self.assertEqual(fact['unresolved_effect_obligation'], 'json_effects_summary_required:json.loads')
        self.assertFalse(graph['source_audit_complete'])

    def test_json_native_io_return_types_keep_writer_and_callback_effects_open(self):
        graph = self.graph({'entry': 'import json\n'
                            'read=json.load(stream)\n'
                            'encoded=json.dumps(value, default=convert)\n'
                            'written=json.dump(value, destination, cls=Encoder)\n'})
        facts = {row['callee']: row for row in graph['builtin_return_facts'] if row['callee'].startswith('json.')}
        self.assertIn('dict', facts['json.load']['output_types'])
        self.assertEqual(facts['json.dumps']['output_types'], ['str'])
        self.assertEqual(facts['json.dump']['output_types'], ['NoneType'])
        self.assertTrue(all(row['unresolved_effect_obligation'] for row in facts.values()))
        self.assertTrue(any(row['name'] == 'default' for row in graph['json_callback_inventory']))
        self.assertTrue(any(row['kind'] == 'json_file_output_effect' for row in graph['edges']))

    def test_json_custom_decoder_and_hooks_never_borrow_native_result_types(self):
        for api in ('loads', 'load'):
            for option in ('cls', 'object_hook', 'object_pairs_hook', 'parse_int', 'parse_float', 'parse_constant'):
                with self.subTest(api=api, option=option):
                    graph = self.graph({'entry': 'import json\nvalue=json.' + api + '(raw, ' + option + '=custom)\n'})
                    self.assertFalse(any(row['callee'] == 'json.' + api for row in graph['builtin_return_facts']))
        import json
        marker = object()
        self.assertIs(json.loads('{}', object_hook=lambda value: marker), marker)
        self.assertIs(json.loads('1', parse_int=lambda value: marker), marker)

    def test_json_custom_encoder_result_and_dump_writer_result_remain_distinct(self):
        import json
        marker = object()
        class Encoder(json.JSONEncoder):
            def encode(self, value):
                return marker
            def iterencode(self, value, _one_shot=False):
                return iter([marker])
        class Writer:
            def __init__(self):
                self.chunks = []
            def write(self, chunk):
                self.chunks.append(chunk)
                return marker
        writer = Writer()
        self.assertIs(json.dumps({}, cls=Encoder), marker)
        self.assertIsNone(json.dump({}, writer, cls=Encoder))
        self.assertEqual(writer.chunks, [marker])
        graph = self.graph({'entry': 'import json\na=json.dumps(value, cls=Encoder)\n'
                            'b=json.dump(value, writer, cls=Encoder)\n'})
        self.assertFalse(any(row['callee'] == 'json.dumps' for row in graph['builtin_return_facts']))
        self.assertEqual(next(row for row in graph['builtin_return_facts'] if row['callee'] == 'json.dump')['output_types'], ['NoneType'])

    def test_json_expanded_arguments_and_shadowed_module_keep_result_open(self):
        for source in ('import json\nvalue=json.loads(raw, **options)\n',
                       'import json\nvalue=json.loads(*args)\n',
                       'import json\njson=unknown\nvalue=json.loads(raw)\n',
                       'import json\nvalue=json.loads(raw, s=other)\n',
                       'import json\nvalue=json.loads(raw, unsupported=other)\n'):
            with self.subTest(source=source):
                graph = self.graph({'entry': source})
                self.assertFalse(any(row['callee'] == 'json.loads' for row in graph['builtin_return_facts']))

    def test_json_result_preconditions_survive_aliases_returns_and_operators(self):
        graph = self.graph({'entry': 'import json\n'
                            'def encode():\n    return json.dumps(raw)\n'
                            'alias=encode()\ncombined=alias+"!"\n'
                            'if combined:\n    observe(combined)\n'})
        required = {'authentic_stdlib_binding:json', 'native_json_encoder_bindings_stable_during_call'}
        returns = [row for row in graph['function_return_facts'] if '::encode@' in row['function']]
        self.assertEqual(len(returns), 1)
        self.assertTrue(required <= set(returns[0]['preconditions']))
        call = next(row for row in graph['local_call_return_facts'] if row['node'] in self.nodes(graph, 'Call', 'encode()'))
        self.assertTrue(required <= set(call['preconditions']))
        addition = next(row for row in graph['primitive_effects'] if row['node'] in self.nodes(graph, 'BinOp', "alias + '!'") and row['operation'] == 'BinOp')
        self.assertTrue(required <= set(addition['preconditions']))
        truth = [row for row in graph['primitive_effects'] if row['operation'] == 'truth_test']
        self.assertTrue(any(required <= set(row.get('preconditions', ())) for row in truth))

    def test_json_root_type_fact_does_not_close_mutated_member_identity(self):
        graph = self.graph({'entry': 'import json, os\nvalue=json.loads(raw)\n'
                            'value["callback"]=os.getpid\n'
                            'fn=value["callback"]\nfn()\n'
                            'nested=value["number"]\nresult=nested+1\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
        self.assertIn(['external', 'os.getpid', ''], call['targets'])
        addition = self.nodes(graph, 'BinOp', 'nested + 1')
        self.assertFalse(any(row['node'] in addition for row in graph['primitive_effects']))

    def test_json_decoder_mutation_during_input_conversion_requires_stability(self):
        source = ('import json\n'
                  'class Marker: pass\n'
                  'class Replacement:\n    def decode(self, text): return Marker()\n'
                  'class Input(str):\n'
                  '    def startswith(self, prefix):\n'
                  '        json._default_decoder=Replacement()\n'
                  '        return False\n'
                  'print(type(json.loads(Input("{}"))).__name__)\n')
        run = subprocess.run([sys.executable, '-B', '-c', source], capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), 'Marker')
        graph = self.graph({'entry': source})
        fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'json.loads')
        self.assertIn('native_json_decoder_bindings_stable_during_call', fact['preconditions'])
        self.assertTrue(any(row['reason'] == 'external_attribute_write_summary_required:_default_decoder'
                            for row in graph['unclassified']))

    def test_json_result_conditions_do_not_spread_to_unrelated_literals(self):
        graph = self.graph({'entry': 'from json import loads as decode\nnone=None\n'
                            'value=decode(s=raw, cls=none)\n'
                            'literal="safe"\nresult=literal+"!"\n'})
        fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'json.loads')
        self.assertIn('native_json_decoder_bindings_stable_during_call', fact['preconditions'])
        literal = next(row for row in graph['primitive_effects'] if row['node'] in self.nodes(graph, 'BinOp', "literal + '!'") and row['operation'] == 'BinOp')
        self.assertNotIn('preconditions', literal)

    def test_json_local_hook_result_types_match_successful_native_roots(self):
        import json
        def pairs(items):
            return ('object',)
        def integer(text):
            return b'number'
        def floating(text):
            return 1j
        def constant(text):
            raise ValueError(text)
        observed = set()
        for raw in ('null', 'true', 'false', '1', '1.5', '"text"', '[]', '{}', 'NaN', 'Infinity'):
            try:
                value = json.loads(raw, object_pairs_hook=pairs, parse_int=integer,
                                   parse_float=floating, parse_constant=constant)
            except ValueError:
                continue
            observed.add(type(value).__name__)
        graph = self.graph({'entry': 'import json\n'
                            'def pairs(items): return ("object",)\n'
                            'def integer(text): return b"number"\n'
                            'def floating(text): return 1j\n'
                            'def constant(text): raise ValueError(text)\n'
                            'value=json.loads(raw, object_pairs_hook=pairs, parse_int=integer, '
                            'parse_float=floating, parse_constant=constant)\n'})
        fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'json.loads')
        self.assertEqual(set(fact['output_types']), observed)
        self.assertEqual(fact['result_contract'], 'json_successful_result.v2')
        self.assertEqual(len(fact['callback_results']), 4)
        self.assertIn('json_callback_bodies_stable_during_call', fact['preconditions'])
        self.assertEqual(fact['unresolved_effect_obligation'], 'json_effects_summary_required:json.loads')
        constant_row = next(row for row in fact['callback_results'] if row['name'] == 'parse_constant')
        self.assertTrue(constant_row['functions'][0]['never_returns'])
        self.assertEqual(constant_row['output_types'], [])

    def test_json_pairs_hook_precedence_does_not_require_unselected_hook_result(self):
        import json
        self.assertEqual(json.loads('{}', object_pairs_hook=lambda items: [],
                                    object_hook=lambda obj: self.fail('unselected hook executed')), [])
        graph = self.graph({'entry': 'import json\ndef pairs(items): return []\n'
                            'value=json.loads(raw, object_pairs_hook=pairs, object_hook=unknown)\n'})
        fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'json.loads')
        self.assertNotIn('dict', fact['output_types'])
        self.assertEqual([r['name'] for r in fact['callback_results']], ['object_pairs_hook'])
        self.assertTrue(any(r['name'] == 'object_hook' for r in graph['json_callback_inventory']))
        self.assertTrue(any(r['reason'] == 'json_callback_selection_summary_required:object_hook'
                            for r in graph['unclassified']))

    def test_json_callback_normal_exit_is_not_confused_with_always_raise(self):
        for body, expected, never in (
                ('    raise ValueError(text)\n', [], True),
                ('    try:\n        raise ValueError(text)\n    except ValueError:\n        pass\n', ['NoneType'], False),
                ('    try:\n        raise ValueError(text)\n    finally:\n        return []\n', ['list'], False)):
            with self.subTest(body=body):
                graph = self.graph({'entry': 'import json\ndef constant(text):\n' + body +
                                    'value=json.loads(raw, parse_constant=constant)\n'})
                fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'json.loads')
                callback = fact['callback_results'][0]
                self.assertEqual(callback['output_types'], expected)
                self.assertEqual(callback['functions'][0]['never_returns'], never)

    def test_json_unresolved_or_suspended_callback_results_stay_open(self):
        for definition in ('def hook(value): return unknown\n',
                           'def hook(value): yield {}\n',
                           'async def hook(value): return {}\n',
                           'def known(value): return {}\nhook=known if flag else unknown\n',
                           'class Hook:\n    def __call__(self, value): return {}\nhook=Hook()\n'):
            with self.subTest(definition=definition):
                graph = self.graph({'entry': 'import json\n' + definition +
                                    'value=json.loads(raw, object_hook=hook)\n'})
                self.assertFalse(any(row['callee'] == 'json.loads' for row in graph['builtin_return_facts']))

    def test_json_float_callback_result_carries_native_conversion_conditions(self):
        import warnings
        class FloatSubclass(float):
            pass
        class Conversion:
            def __float__(self):
                return FloatSubclass(1.25)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            self.assertIs(type(float(Conversion())), float)
        graph = self.graph({'entry': 'import json\n'
                            'def floating(text): return float(text)\n'
                            'def decode(): return json.loads(raw, parse_float=floating)\n'
                            'value=decode()\n'})
        fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'json.loads')
        required = {'authentic_builtin_binding:float', 'authentic_stdlib_binding:json',
                    'native_json_decoder_bindings_stable_during_call', 'json_callback_bodies_stable_during_call'}
        self.assertTrue(required <= set(fact['preconditions']))
        self.assertEqual(fact['callback_results'][0]['output_types'], ['float'])
        returned = next(row for row in graph['function_return_facts'] if '::decode@' in row['function'])
        self.assertTrue(required <= set(returned['preconditions']))
        call = next(row for row in graph['local_call_return_facts'] if row['node'] in self.nodes(graph, 'Call', 'decode()'))
        self.assertTrue(required <= set(call['preconditions']))
        conversion = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'builtins.float')
        self.assertEqual(conversion['unresolved_effect_obligation'], 'external_api_summary_required:builtins.float')

    def test_json_callback_body_mutation_requires_its_own_stability_condition(self):
        source = ('import json\nclass Marker: pass\n'
                  'def replacement(items): return Marker()\n'
                  'def hook(items):\n    hook.__code__=replacement.__code__\n    return {}\n'
                  'print(type(json.loads(\'{"inner":{}}\', object_pairs_hook=hook)).__name__)\n')
        run = subprocess.run([sys.executable, '-B', '-c', source], capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), 'Marker')
        graph = self.graph({'entry': source})
        fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'json.loads')
        self.assertIn('json_callback_bodies_stable_during_call', fact['preconditions'])
        self.assertTrue(any(row['node'] == fact['node'] and row['reason'] == 'json_callback_body_stability_summary_required'
                            for row in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])

    def test_json_local_callback_alternatives_keep_every_successful_result(self):
        graph = self.graph({'entry': 'import json\n'
                            'def left(items): return {}\ndef right(items): return ()\n'
                            'hook=left if flag else right\nvalue=json.loads(raw, object_hook=hook)\n'})
        fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'json.loads')
        callback = fact['callback_results'][0]
        self.assertEqual(callback['output_types'], ['dict', 'tuple'])
        self.assertEqual(len(callback['functions']), 2)
        self.assertTrue(all(row['return_slot'] in fact['inputs'] for row in callback['functions']))

    def test_json_typed_hook_does_not_certify_mutable_nested_member(self):
        graph = self.graph({'entry': 'import json, os\n'
                            'def pairs(items): return {}\n'
                            'value=json.loads(raw, object_pairs_hook=pairs)\n'
                            'value["callback"]=os.getpid\nfn=value["callback"]\nfn()\n'
                            'result=value["number"]+1\n'})
        fact = next(row for row in graph['builtin_return_facts'] if row['callee'] == 'json.loads')
        self.assertIn('dict', fact['output_types'])
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
        self.assertIn(['external', 'os.getpid', ''], call['targets'])
        addition = self.nodes(graph, 'BinOp', "value['number'] + 1")
        self.assertFalse(any(row['node'] in addition for row in graph['primitive_effects']))

    def test_successful_type_guard_refines_return_and_local_caller(self):
        source = ('def require(condition):\n    if not condition: raise ValueError()\n'
                  'def parse(value):\n    require(type(value) is dict)\n    return value\n'
                  'result=parse(raw)\n')
        graph = self.graph({'entry': source})
        returned = next(r for r in graph['function_return_facts'] if '::parse@' in r['function'])
        self.assertEqual(returned['output_types'], ['dict'])
        self.assertTrue(any(p.startswith('authentic_guard_callable_body:') for p in returned['preconditions']))
        self.assertTrue(any(p.startswith('guarded_local_binding_stable_during_and_after_check:') for p in returned['preconditions']))
        call = next(r for r in graph['local_call_return_facts'] if r['node'] in self.nodes(graph, 'Call', 'parse(raw)'))
        self.assertEqual(call['output_facts'], ['type:dict'])
        self.assertEqual(call['preconditions'], returned['preconditions'])
        self.assertTrue(any(r['reason'] == 'successful_type_guard_bindings_summary_required' for r in graph['unclassified']))

    def test_direct_exact_type_guards_follow_only_surviving_branch(self):
        for condition in ('type(value) is not bytes', 'not (type(value) is bytes)',
                          'bytes is not type(value)', 'type(value) is not bytes or flag'):
            with self.subTest(condition=condition):
                graph = self.graph({'entry': 'def parse(value):\n    if ' + condition +
                                    ':\n        raise ValueError()\n    return value\n'})
                returned = next(r for r in graph['function_return_facts'] if '::parse@' in r['function'])
                self.assertEqual(returned['output_types'], ['bytes'])
                self.assertIn('authentic_builtin_binding:type', returned['preconditions'])

    def test_type_guard_join_requires_every_normal_path(self):
        guard = 'def require(condition):\n    if not condition: raise ValueError()\n'
        for body, expected in (
                ('    if flag:\n        require(type(value) is dict)\n', None),
                ('    if flag:\n        require(type(value) is dict)\n    else:\n        require(type(value) is list)\n', ['dict', 'list'])):
            graph = self.graph({'entry': guard+'def parse(value):\n'+body+'    return value\n'})
            returned = [r for r in graph['function_return_facts'] if '::parse@' in r['function']]
            self.assertEqual(returned[0]['output_types'] if returned else None, expected)

    def test_type_guard_local_rebinding_kills_the_path_fact(self):
        guard = 'def require(condition, code=None):\n    if not condition: raise ValueError()\n'
        for middle in ('    value=[]\n', '    del value\n', '    value += []\n',
                       '    (value := [])\n', '    assert (value := [])\n',
                       '    import value\n', '    def value(): pass\n'):
            with self.subTest(middle=middle):
                source=guard+'def parse(value):\n    require(type(value) is dict)\n'+middle+'    return value\n'
                graph=self.graph({'entry':source})
                last_line=len(source.splitlines())
                self.assertFalse(any(graph['nodes'][r['node']]['line']==last_line
                                     for r in graph['successful_type_guard_inventory']))
        source=guard+'def parse(value):\n    require(type(value) is dict, (value := []))\n    return value\n'
        self.assertEqual(self.graph({'entry':source})['successful_type_guard_inventory'], [])

    def test_type_guard_caught_failure_does_not_certify_handler_return(self):
        source=('def require(condition):\n    if not condition: raise ValueError()\n'
                'def parse(value):\n    try:\n        require(type(value) is dict)\n        return value\n'
                '    except ValueError:\n        return value\n')
        run = subprocess.run([sys.executable, '-B', '-c', source + '\nprint(parse([]))\n'],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), '[]')
        graph=self.graph({'entry':source})
        self.assertFalse(any('::parse@' in r['function'] for r in graph['function_return_facts']))
        self.assertTrue(any(graph['nodes'][r['node']]['line']==6 for r in graph['successful_type_guard_inventory']))
        self.assertFalse(any(graph['nodes'][r['node']]['line']==8 for r in graph['successful_type_guard_inventory']))

    def test_type_guard_finally_and_context_suppression_do_not_borrow_normal_state(self):
        guard='def require(condition):\n    if not condition: raise ValueError()\n'
        for body in ('    try:\n        require(type(value) is dict)\n        return value\n    finally:\n        return value\n',
                     '    with manager:\n        require(type(value) is dict)\n    return value\n',
                     '    for item in items:\n        require(type(value) is dict)\n    return value\n'):
            graph=self.graph({'entry':guard+'def parse(value):\n'+body})
            self.assertFalse(any('::parse@' in r['function'] for r in graph['function_return_facts']))

    def test_type_guard_uses_closed_helper_and_builtin_identities(self):
        for prefix, predicate in (
                ('def require(condition): pass\n', 'type(value) is dict'),
                ('def require(condition):\n    if not condition: print("ignored")\n', 'type(value) is dict'),
                ('def require(condition):\n    if not condition: raise ValueError()\ndef type(value): return dict\n', 'type(value) is dict'),
                ('def require(condition):\n    if not condition: raise ValueError()\nclass dict: pass\n', 'type(value) is dict'),
                ('def require(condition):\n    if not condition: raise ValueError()\n', 'isinstance(value, dict)'),
                ('def require(condition):\n    if not condition: raise ValueError()\n', 'type(value) == dict')):
            with self.subTest(prefix=prefix,predicate=predicate):
                graph=self.graph({'entry':prefix+'def parse(value):\n    require('+predicate+')\n    return value\n'})
                self.assertFalse(any('::parse@' in r['function'] for r in graph['function_return_facts']))

    def test_type_guard_import_alias_and_keyword_binding_are_resolved(self):
        graph=self.graph({'helpers':'def require(*, condition):\n    if not condition: raise ValueError()\n',
                          'entry':'from helpers import require as check\nfrom builtins import type as kind\n'
                                  'def parse(value):\n    check(condition=kind(value) is dict)\n    return value\n'})
        returned=next(r for r in graph['function_return_facts'] if '::parse@' in r['function'])
        self.assertEqual(returned['output_types'], ['dict'])
        for declaration, call in (
                ('def require(condition=True, /, **kwargs):\n    if not condition: raise ValueError()\n', 'require(condition=type(value) is dict)'),
                ('def require(condition):\n    if not condition: raise ValueError()\n', 'require(*(type(value) is dict,))')):
            graph=self.graph({'entry':declaration+'def parse(value):\n    '+call+'\n    return value\n'})
            self.assertFalse(any('::parse@' in r['function'] for r in graph['function_return_facts']))

    def test_assert_does_not_supply_an_optimization_stable_type_guard(self):
        source='def parse(value):\n    assert type(value) is dict\n    return value\nprint(type(parse([])).__name__)\n'
        run=subprocess.run([sys.executable,'-B','-O','-c',source],capture_output=True,text=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(run.stdout.strip(),'list')
        self.assertEqual(self.graph({'entry':source})['successful_type_guard_inventory'],[])

    def test_type_guard_retains_actual_nonlocal_rebinding_as_an_obligation(self):
        source=('def require(condition):\n    if not condition: raise ValueError()\n'
                'def parse(value):\n    def change():\n        nonlocal value\n        value=[]\n'
                '    require(type(value) is dict)\n    change()\n    return value\n')
        run = subprocess.run([sys.executable, '-B', '-c', source + '\nprint(parse({}))\n'],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), '[]')
        graph=self.graph({'entry':source})
        returned=next(r for r in graph['function_return_facts'] if '::parse@' in r['function'])
        self.assertIn('dict',returned['output_types'])
        self.assertTrue(any(p.startswith('guarded_local_binding_stable_during_and_after_check:') for p in returned['preconditions']))
        self.assertTrue(any(r['reason']=='successful_type_guard_bindings_summary_required' for r in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])

    def test_type_guard_requires_the_actual_declared_helper_body(self):
        source=('def require(condition):\n    if not condition: raise ValueError()\n'
                'def ignored(condition): pass\nrequire.__code__=ignored.__code__\n'
                'def parse(value):\n    require(type(value) is dict)\n    return value\n')
        run = subprocess.run([sys.executable, '-B', '-c', source + '\nprint(parse([]))\n'],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), '[]')
        graph=self.graph({'entry':source})
        returned=next(r for r in graph['function_return_facts'] if '::parse@' in r['function'])
        self.assertTrue(any(p.startswith('authentic_guard_callable_body:') for p in returned['preconditions']))
        self.assertTrue(any(p.startswith('guard_callable_body_stable_during_call:') for p in returned['preconditions']))
        self.assertFalse(graph['source_audit_complete'])

    def test_actual_strict_json_source_returns_dict_under_guard_conditions(self):
        import ast
        import verify_live_cross_domain_evidence_round_trip_release as bootstrap
        source=Path(bootstrap.__file__).read_text();tree=ast.parse(source)
        selected=[ast.get_source_segment(source,node) for node in tree.body
                  if isinstance(node,ast.FunctionDef) and node.name in ('require','strict_json','stored')]
        graph=self.graph({'entry':'import json, math\n'+'\n\n'.join(selected)})
        returned=next(r for r in graph['function_return_facts'] if '::strict_json@' in r['function'])
        self.assertEqual(returned['output_types'],['dict'])
        self.assertIn('authentic_builtin_binding:dict',returned['preconditions'])
        self.assertEqual(bootstrap.strict_json(b'{}\n'),{})
        with self.assertRaises(ValueError):bootstrap.strict_json(b'[]\n')

    def test_actual_candidate_graph_binds_source_without_executing_it(self):
        import ast
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as bootstrap
        sys.path[:] = previous
        sources = {'proof_kernel/' + name + '.py': (CONTRACT_PATH.parent / (name + '.py')).read_bytes()
                   for name in bootstrap.LOCAL_MODULES}
        graph = bootstrap.PythonInputFlowGraph(sources).build()
        self.assertEqual({row['path']: row['sha256'] for row in graph['files']},
                         {path: hashlib.sha256(raw).hexdigest() for path, raw in sources.items()})
        self.assertGreater(len(graph['calls']), 4000)
        syntax = [node for raw in sources.values() for node in ast.walk(ast.parse(raw))]
        self.assertEqual(sum(isinstance(node, ast.Call) for node in syntax),
                         sum(graph['nodes'][row['node']]['kind'] == 'Call' for row in graph['calls']))
        self.assertEqual(sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) for node in syntax),
                         sum(row['kind'] == 'function_definition' for row in graph['nodes']))
        self.assertTrue(all(row['path'] in sources for row in graph['nodes']))
        self.assertTrue(graph['unclassified'])
        self.assertFalse(graph['source_audit_complete'])

    def test_append_and_extend_keep_callable_aliases_through_container_fields(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'class Box:\n'
                            '    def __init__(self):\n        self.callbacks = []\n'
                            '    def add(self, fn):\n        self.callbacks.append(fn)\n'
                            '    def call(self):\n        alias = self.callbacks[0]\n        return alias()\n'
                            'box = Box()\nbox.add(os.getpid)\nbox.call()\n'
                            'callbacks = []\ncallbacks.extend([time.monotonic])\n'
                            'from_extend = callbacks[0]\nfrom_extend()\n'})
        for label, expected in [('alias()', 'os.getpid'), ('from_extend()', 'time.monotonic')]:
            call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
            self.assertEqual(call['targets'], [['external', expected, '']])

    def test_dictionary_get_and_setdefault_preserve_selected_and_fallback_aliases(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'table = {"fn": os.getpid, "other": time.monotonic}\n'
                            'alias = table.get("fn")\nalias()\n'
                            'fallback = table.setdefault("missing", time.monotonic)\nfallback()\n'
                            'retained = table["missing"]\nretained()\n'})
        for label, expected in [('alias()', 'os.getpid'), ('fallback()', 'time.monotonic'),
                                ('retained()', 'time.monotonic')]:
            call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
            self.assertEqual(call['targets'], [['external', expected, '']])

    def test_dictionary_iteration_and_views_keep_keys_separate_from_values(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'table = {os.getpid: time.monotonic}\n'
                            'for key in table:\n    key()\n'
                            'for key_view in table.keys():\n    key_view()\n'
                            'for value_view in table.values():\n    value_view()\n'
                            'for pair_key, pair_value in table.items():\n    pair_key()\n    pair_value()\n'})
        for label, expected in [('key()', 'os.getpid'), ('key_view()', 'os.getpid'),
                                ('value_view()', 'time.monotonic'), ('pair_key()', 'os.getpid'),
                                ('pair_value()', 'time.monotonic')]:
            call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
            self.assertEqual(call['targets'], [['external', expected, '']])

    def test_dictionary_comprehension_retains_separate_key_and_value_aliases(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'table = {key: time.monotonic for key in [os.getpid]}\n'
                            'for key in table:\n    key()\n'
                            'for value in table.values():\n    value()\n'})
        for label, expected in [('key()', 'os.getpid'), ('value()', 'time.monotonic')]:
            call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
            self.assertEqual(call['targets'], [['external', expected, '']])

    def test_copy_update_and_pop_retain_possible_values_without_aliasing_keys(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'original = {"fn": os.getpid}\ncopy = original.copy()\n'
                            'copy.update({"fn": time.monotonic})\n'
                            'alias = copy.pop("fn")\nalias()\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'alias()'))
        self.assertEqual(call['targets'], [['external', 'os.getpid', ''], ['external', 'time.monotonic', '']])

    def test_branch_control_reaches_container_method_write(self):
        graph = self.graph({'entry': 'import os\n'
                            'def choose():\n'
                            '    owners = []\n'
                            '    if os.getpid():\n        owners.append("A")\n'
                            '    return owners[0]\n'})
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                       self.nodes(graph, 'return_slot', function='choose')))

    def test_custom_get_method_is_not_assumed_to_be_a_dictionary_operation(self):
        graph = self.graph({'entry': 'def lookup(unknown):\n    return unknown.get("owner")\n'})
        call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', "unknown.get('owner')"))
        self.assertEqual(call['targets'], [])
        self.assertTrue(any(row['node'] == call['node'] and row['reason'] == 'call_target_unresolved'
                            for row in graph['unclassified']))

    def test_container_alias_graph_does_not_silently_accept_element_callbacks(self):
        graph = self.graph({'entry': 'class Key:\n'
                            '    def __hash__(self):\n        return 1\n'
                            'table = {}\nvalue = table.get(Key())\n'})
        self.assertTrue(any(row['reason'] == 'container_element_protocol_summary_required:dict.get'
                            for row in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])

    def test_conditional_expression_and_short_circuit_control_helper_effects(self):
        for expression in ('write() if os.getpid() else None', 'os.getpid() and write()',
                           'os.getpid() or write()'):
            with self.subTest(expression=expression):
                graph = self.graph({'entry': 'import os\nowner = "B"\n'
                                    'def write():\n    global owner\n    owner = "A"\n' + expression + '\n'})
                self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'),
                                               self.nodes(graph, 'symbol', 'owner', '<module>')))

    def test_sorted_key_callback_is_traced_without_becoming_a_selected_callable(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'def key(value):\n    return time.monotonic()\n'
                            'ordered = sorted([os.getpid], key=key)\n'
                            'selected = ordered[0]\nselected()\n'})
        callback = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'implicit_call', 'builtins.sorted.callback'))
        self.assertTrue(any(target[0] == 'function' and '::key@' in target[1] for target in callback['targets']))
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'time.monotonic()'),
                                       self.nodes(graph, 'symbol', 'ordered')))
        selected = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'selected()'))
        self.assertEqual(selected['targets'], [['external', 'os.getpid', '']])

    def test_map_callback_argument_return_and_side_effect_are_all_traced(self):
        graph = self.graph({'entry': 'import os\nowner = "B"\n'
                            'def relay(value):\n    global owner\n    owner = value\n    return value\n'
                            'mapped = map(relay, [os.getpid])\n'
                            'for fn in mapped:\n    fn()\n'})
        selected = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
        self.assertEqual(selected['targets'], [['external', 'os.getpid', '']])
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Attribute', 'os.getpid'),
                                       self.nodes(graph, 'symbol', 'owner', '<module>')))

    def test_sorted_comparison_follows_key_result_and_preserves_selected_elements(self):
        graph = self.graph({'entry': 'import os\nowner = 0\n'
                            'class Key:\n'
                            '    def __lt__(self, other):\n        global owner\n        owner = os.getpid()\n        return True\n'
                            'def key(value):\n    return Key()\n'
                            'ordered = sorted([os.getpid], key=key)\nordered[0]()\n'})
        row = graph['sorted_protocol_inventory'][0]
        callbacks = [edge for edge in graph['builtin_protocol_edges'] if edge['builtin'] == 'sorted_compare']
        self.assertTrue(any(edge['method'] == '__lt__' and '::Key.__lt__@' in edge['target_definition'] for edge in callbacks))
        owner = self.nodes(graph, 'symbol', 'owner', '<module>')
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), owner))
        self.assertTrue(self.reachable(graph, [row['node']], owner))
        selected = next(call for call in graph['calls'] if call['node'] in self.nodes(graph, 'Call', 'ordered[0]()'))
        self.assertEqual(selected['targets'], [['external', 'os.getpid', '']])
        self.assertFalse(row['native_effects_accepted'])

    def test_sorted_comparison_traces_reflected_slot_without_claiming_dispatch_order(self):
        graph = self.graph({'entry': 'import os\n'
                            'class Key:\n'
                            '    def __lt__(self, other):\n        return NotImplemented\n'
                            '    def __gt__(self, other):\n        return os.getpid()\n'
                            'ordered = sorted([Key(), Key()])\n'})
        methods = {edge['method'] for edge in graph['builtin_protocol_edges'] if edge['builtin'] == 'sorted_compare'}
        self.assertEqual(methods, {'__lt__', '__gt__'})
        row = graph['sorted_protocol_inventory'][0]
        self.assertIsNone(row['key_callback_node'])
        self.assertIn('rich_comparison_dispatch_and_effects', row['preconditions'])
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), [row['node']]))

    def test_sorted_comparison_truth_result_is_traced_without_aliasing_output(self):
        graph = self.graph({'entry': 'import os\n'
                            'class Verdict:\n'
                            '    def __bool__(self):\n        return bool(os.getpid())\n'
                            'class Key:\n'
                            '    def __lt__(self, other):\n        return Verdict()\n'
                            'def key(value):\n    return Key()\n'
                            'ordered = sorted([os.getpid], key=key)\nordered[0]()\n'})
        self.assertTrue(any(edge['builtin'] == 'sorted_truth' and '::Verdict.__bool__@' in edge['target_definition']
                            for edge in graph['builtin_protocol_edges']))
        row = graph['sorted_protocol_inventory'][0]
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), [row['node']]))
        selected = next(call for call in graph['calls'] if call['node'] in self.nodes(graph, 'Call', 'ordered[0]()'))
        self.assertEqual(selected['targets'], [['external', 'os.getpid', '']])

    def test_sorted_reverse_conversion_keeps_runtime_variants_and_bool_precedence(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'class Reverse:\n'
                            '    def __bool__(self):\n        return bool(os.getpid())\n'
                            '    def __index__(self):\n        return os.getpid()\n'
                            '    def __len__(self):\n        return int(time.monotonic())\n'
                            'ordered = sorted([1, 2], reverse=Reverse())\n'})
        row = graph['sorted_protocol_inventory'][0]
        callbacks = [edge for edge in graph['builtin_protocol_edges'] if edge['builtin_node'] == row['reverse_conversion_node']]
        self.assertEqual({edge['method'] for edge in callbacks}, {'__bool__', '__index__'})
        self.assertIn('reverse_conversion_matches_runtime', row['preconditions'])
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), [row['node']]))

    def test_sorted_length_hint_is_an_input_effect(self):
        graph = self.graph({'entry': 'import os\n'
                            'class Source:\n'
                            '    def __iter__(self):\n        return self\n'
                            '    def __next__(self):\n        return 1\n'
                            '    def __length_hint__(self):\n        return os.getpid()\n'
                            'ordered = sorted(Source())\n'})
        row = graph['sorted_protocol_inventory'][0]
        self.assertTrue(any(edge['builtin'] == 'sorted_length_hint' and edge['method'] == '__length_hint__'
                            for edge in graph['builtin_protocol_edges']))
        self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', 'os.getpid()'), [row['node']]))

    def test_sorted_nested_tuple_comparisons_trace_equality_order_and_truth(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'class Result:\n'
                            '    def __bool__(self):\n        return bool(os.getpid())\n'
                            'class Key:\n'
                            '    def __eq__(self, other):\n        return Result()\n'
                            '    def __lt__(self, other):\n        return bool(time.monotonic())\n'
                            'def key(value):\n    return ((Key(),), value)\n'
                            'ordered = sorted([1, 2], key=key)\n'})
        row = graph['sorted_protocol_inventory'][0]
        self.assertEqual({item['operation'] for item in row['element_comparisons']}, {'Eq', 'Lt'})
        self.assertEqual(len({item['container'] for item in row['element_comparisons']}), 2)
        methods = {edge['method'] for edge in graph['builtin_protocol_edges'] if edge['builtin'] == 'sorted_compare'}
        self.assertTrue({'__eq__', '__lt__'} <= methods)
        for label in ('os.getpid()', 'time.monotonic()'):
            self.assertTrue(self.reachable(graph, self.nodes(graph, 'Call', label), [row['node']]))

    def test_sorted_recursive_list_comparison_inventory_terminates(self):
        graph = self.graph({'entry': 'values = []\nvalues.append(values)\nordered = sorted([values, values])\n'})
        row = graph['sorted_protocol_inventory'][0]
        self.assertEqual(len(row['element_comparisons']), 2)
        self.assertFalse(graph['source_audit_complete'])

    def test_sorted_invalid_or_expanded_binding_does_not_get_a_protocol_inventory(self):
        for expression in ('sorted([], [], key=None)', 'sorted([], surprise=1)', 'sorted(*args)', 'sorted([], **kwargs)'):
            with self.subTest(expression=expression):
                graph = self.graph({'entry': expression + '\n'})
                self.assertEqual(graph['sorted_protocol_inventory'], [])
                self.assertTrue(any(row['reason'] == 'external_api_summary_required:builtins.sorted'
                                    for row in graph['unclassified']))

    def test_sorted_key_temporary_finalizers_remain_an_explicit_obligation(self):
        graph = self.graph({'entry': 'import os\n'
                            'class Key:\n'
                            '    def __del__(self):\n        os.getpid()\n'
                            'def key(value):\n    return Key()\n'
                            'ordered = sorted([1], key=key)\n'})
        row = graph['sorted_protocol_inventory'][0]
        self.assertIn('temporary_release_and_finalizer_effects', row['preconditions'])
        self.assertFalse(row['native_effects_accepted'])
        self.assertTrue(any(item['node'] == row['node'] and item['reason'] == 'external_api_summary_required:builtins.sorted'
                            for item in graph['unclassified']))

    def test_explicit_none_key_records_element_protocol_without_a_phantom_call(self):
        graph = self.graph({'entry': 'ordered = sorted([1], key=None)\n'})
        self.assertFalse(self.nodes(graph, 'implicit_call'))
        self.assertTrue(any(row['reason'] == 'builtin_element_protocol_summary_required:builtins.sorted'
                            for row in graph['unclassified']))

    def test_builtin_container_constructors_keep_iterated_aliases(self):
        for expression in ('list([os.getpid])', 'tuple([os.getpid])', 'set([os.getpid])',
                           'frozenset([os.getpid])'):
            with self.subTest(expression=expression):
                graph = self.graph({'entry': 'import os\nvalues = ' + expression + '\nfor fn in values:\n    fn()\n'})
                call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', 'fn()'))
                self.assertEqual(call['targets'], [['external', 'os.getpid', '']])

    def test_starred_container_and_dictionary_expansion_keep_values(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'source = [os.getpid]\nexpanded = [*source]\n'
                            'alias = expanded[0]\nalias()\n'
                            'mapping = {"fn": time.monotonic}\nmerged = {**mapping}\n'
                            'lookup = merged["fn"]\nlookup()\n'})
        for label, expected in [('alias()', 'os.getpid'), ('lookup()', 'time.monotonic')]:
            call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
            self.assertEqual(call['targets'], [['external', expected, '']])

    def test_dictionary_constructor_tracks_mapping_keywords_and_pair_values(self):
        graph = self.graph({'entry': 'import os, time\n'
                            'mapping = dict(fn=os.getpid)\nfrom_keyword = mapping["fn"]\nfrom_keyword()\n'
                            'copied = dict(mapping)\nfrom_mapping = copied["fn"]\nfrom_mapping()\n'
                            'paired = dict([(os.getpid, time.monotonic)])\n'
                            'for pair_key in paired:\n    pair_key()\n'
                            'for pair_value in paired.values():\n    pair_value()\n'})
        for label, expected in [('from_keyword()', 'os.getpid'), ('from_mapping()', 'os.getpid'),
                                ('pair_key()', 'os.getpid'), ('pair_value()', 'time.monotonic')]:
            call = next(row for row in graph['calls'] if row['node'] in self.nodes(graph, 'Call', label))
            self.assertEqual(call['targets'], [['external', expected, '']])
        self.assertTrue(any(row['reason'] == 'mapping_pair_shape_summary_required' for row in graph['unclassified']))

    def call_bindings(self, graph, function):
        return [row for row in graph['call_argument_binding_inventory'] if '::' + function + '@' in row['function']]

    def local_types(self, graph, name, function):
        return [row for row in graph['successful_local_type_inventory'] if row['name']==name
                and graph['nodes'][row['node']]['function']==function]

    def call_contexts(self, graph, function):
        return [row for row in graph['call_context_type_inventory'] if '::'+function+'@' in row['function']]

    def expanded_contexts(self, graph, function):
        bindings = graph['call_argument_binding_inventory']
        return [row for row in graph['call_context_closure']['contexts']
                if '::'+function+'@' in bindings[row['binding_index']]['function']]

    def expanded_conditions(self, graph, row):
        closure = graph['call_context_closure']
        return {closure['condition_inventory'][number]
                for number in closure['condition_sets'][row['required_condition_set']]}

    def dictionary_comparisons(self, graph, function):
        return [r for r in graph['context_dictionary_comparison_inventory'] if '::'+function+'@' in r['function']]

    def test_context_dictionary_comparison_binds_actual_helper_operands(self):
        graph=self.graph({'entry':'def expected(): return {}\ndef check(record):\n'
                          '    if record != expected(): raise ValueError("bad")\n'
                          'def outer(value): return check(value)\na=outer({})\n'})
        rows=[r for r in self.dictionary_comparisons(graph,'check') if r['status']=='conditional_successful_bool']
        self.assertEqual(len(rows),1)
        row=rows[0]
        self.assertEqual(row['operations'],['NotEq']);self.assertEqual(row['output_types'],['bool'])
        self.assertEqual([r['output_types'] for r in row['operands']],[['dict'],['dict']])
        self.assertEqual(row['operands'][0]['fact_origin'],'contextual_read')
        self.assertTrue(any(p.startswith('call_context_body_binding_stable:') and '::expected@' in p for p in row['preconditions']))
        self.assertTrue(row['truth_destinations']);self.assertEqual(row['additional_result_truth_callbacks'],[])
        self.assertTrue(row['truth_inherits_comparison_effects'])

    def test_context_dictionary_comparison_unknown_caller_does_not_borrow_dict(self):
        graph=self.graph({'entry':'def check(record): return record == {}\na=check({})\nb=check(unknown)\n'})
        rows=self.dictionary_comparisons(graph,'check')
        self.assertEqual([r['status'] for r in rows],['conditional_successful_bool','operand_types_unresolved'])
        self.assertEqual(rows[1]['output_types'],[])
        self.assertIsNone(rows[1]['additional_result_truth_callbacks'])

    def test_context_dictionary_comparison_mixed_branch_types_remain_unresolved(self):
        graph=self.graph({'entry':'def check(record,flag):\n    if flag: record=[]\n'
                          '    return record == {}\na=check({},True)\n'})
        row=self.dictionary_comparisons(graph,'check')[0]
        self.assertEqual(row['operands'][0]['output_types'],['dict','list'])
        self.assertEqual(row['status'],'operand_types_unresolved')

    def test_context_dictionary_comparison_chains_keep_all_possible_effects(self):
        graph=self.graph({'entry':'def check(record): return record == {} != {}\na=check({})\n'})
        row=self.dictionary_comparisons(graph,'check')[0]
        self.assertEqual(row['operations'],['Eq','NotEq']);self.assertEqual(len(row['operands']),3)
        self.assertEqual(row['output_types'],['bool'])
        self.assertIn('member_result_truth_conversion',row['potential_effects'])
        self.assertIn('reachable_state_mutation',row['potential_effects'])
        self.assertFalse(row['member_effects_accepted'])

    def test_context_dictionary_comparison_does_not_accept_subclass_override(self):
        class Dictionary(dict):
            def __eq__(self, other):
                return 'custom result'
        self.assertEqual(Dictionary()=={},'custom result')
        graph=self.graph({'entry':'class Dictionary(dict):\n    def __eq__(self,other): return "custom result"\n'
                          'def check(record): return record == {}\na=check(Dictionary())\n'})
        row=self.dictionary_comparisons(graph,'check')[0]
        self.assertEqual(row['status'],'operand_types_unresolved');self.assertEqual(row['output_types'],[])

    def test_native_dictionary_result_is_bool_while_member_callbacks_mutate(self):
        events=[]
        class Truth:
            def __bool__(self):
                events.append('truth');return True
        class Value:
            def __eq__(self, other):
                events.append('equality');return Truth()
            def __ne__(self, other):
                raise AssertionError('dict inequality compares values with equality')
        left={'value':Value()};right={'value':Value()}
        self.assertIs(left==right,True)
        self.assertEqual(events,['equality','truth'])
        events.clear()
        self.assertIs(left!=right,False)
        self.assertEqual(events,['equality','truth'])

    def test_native_dictionary_member_failure_does_not_undo_prior_side_effect(self):
        events=[]
        class Value:
            def __eq__(self, other):
                events.append('effect');raise ValueError('comparison failed')
        with self.assertRaisesRegex(ValueError,'comparison failed'):
            {'value':Value()}=={'value':Value()}
        self.assertEqual(events,['effect'])

    def test_context_dictionary_comparison_retains_global_obligations(self):
        graph=self.graph({'entry':'def check(record):\n    if record == {}: return True\na=check({})\n'})
        row=self.dictionary_comparisons(graph,'check')[0]
        for field in ('member_effects_accepted','operand_evaluation_effects_accepted','global_obligations_removed'):
            self.assertFalse(row[field])
        reasons={r['reason'] for r in graph['unclassified'] if r['node']==row['node']}
        self.assertIn('operand_protocol_summary_required:Compare',reasons)
        self.assertIn('context_dictionary_member_effects_summary_required',reasons)
        edges=[e for e in graph['edges'] if e['kind'].startswith('context_dictionary_')]
        self.assertTrue(edges);self.assertTrue(all(e['reference'] is False for e in edges))
        self.assertFalse(graph['source_audit_complete'])

    def test_context_dictionary_ordering_is_outside_equality_contract(self):
        graph=self.graph({'entry':'def check(record): return record < {}\na=check({})\n'})
        self.assertEqual(self.dictionary_comparisons(graph,'check'),[])
        with self.assertRaises(TypeError):
            {} < {}

    def test_context_closure_traces_three_helpers_with_distinct_entry_types(self):
        graph=self.graph({'entry':'def leaf(x): return x\ndef middle(y): return leaf(y)\n'
                          'def outer(z): return middle(z)\na=outer({})\nb=outer([])\n'})
        closure=graph['call_context_closure']
        for root in self.expanded_contexts(graph,'outer'):
            expected=root['input_facts'][0]['value_facts'][0][5:]
            state=root
            for function in ('middle','leaf'):
                edges=[e for e in closure['edges'] if e['parent_context']==state['id']]
                self.assertEqual(len(edges),1)
                state=closure['contexts'][edges[0]['child_context']]
                self.assertIn(state,self.expanded_contexts(graph,function))
                self.assertEqual(state['reads'][0]['output_types'],[expected])
            self.assertTrue(self.expanded_conditions(graph,root)<=self.expanded_conditions(graph,state))
        self.assertFalse(any('::leaf@' in row['function'] for row in graph['function_return_facts']))

    def test_context_closure_direct_recursion_retains_cycle_without_termination_claim(self):
        graph=self.graph({'entry':'def again(value): return again(value)\na=again({})\n'})
        closure=graph['call_context_closure']
        loops=[e for e in closure['edges'] if e['parent_context']==e['child_context']]
        self.assertTrue(loops)
        self.assertTrue(any(closure['contexts'][e['child_context']]['input_facts'][0]['value_facts']==['type:dict'] for e in loops))
        self.assertTrue(closure['context_fixed_point_reached'])
        self.assertFalse(closure['recursion_termination_proven'])
        self.assertFalse(closure['execution_proven'])

    def test_context_closure_mutual_recursion_preserves_both_bodies_conditions(self):
        graph=self.graph({'entry':'def left(value): return right(value)\ndef right(item): return left(item)\na=left({})\n'})
        closure=graph['call_context_closure'];pairs={(e['parent_context'],e['child_context']) for e in closure['edges']}
        cycles=[(a,b) for a,b in pairs if (b,a) in pairs and a!=b]
        self.assertTrue(cycles)
        for a,b in cycles:
            self.assertEqual(self.expanded_conditions(graph,closure['contexts'][a]),self.expanded_conditions(graph,closure['contexts'][b]))
            conditions=self.expanded_conditions(graph,closure['contexts'][a])
            self.assertTrue(any('::left@' in p for p in conditions))
            self.assertTrue(any('::right@' in p for p in conditions))

    def test_context_closure_recursive_type_change_gets_a_distinct_state(self):
        graph=self.graph({'entry':'def again(value):\n    again([])\n    return value\na=again({})\n'})
        rows=self.expanded_contexts(graph,'again')
        self.assertEqual({tuple(r['input_facts'][0]['value_facts']) for r in rows},{('type:dict',),('type:list',)})
        for row in rows:
            expected=[v[5:] for v in row['input_facts'][0]['value_facts']]
            self.assertEqual(row['reads'][-1]['output_types'],expected)

    def test_context_closure_shared_helper_retains_every_parent_origin(self):
        graph=self.graph({'entry':'def leaf(x): return x\ndef outer(value): return leaf(value)\na=outer({})\nb=outer({})\n'})
        closure=graph['call_context_closure'];parents=self.expanded_contexts(graph,'outer')
        edges=[e for e in closure['edges'] if e['parent_context'] in {r['id'] for r in parents}]
        self.assertEqual(len(edges),2)
        self.assertEqual(len({e['child_context'] for e in edges}),1)
        self.assertEqual(len({e['parent_context'] for e in edges}),2)
        origins=[set(self.call_contexts(graph,'outer')[i]['entry_bindings'][0]['inputs']) for i in range(2)]
        self.assertFalse(origins[0]&origins[1])

    def test_context_closure_unknown_entry_still_traces_constant_local_helper(self):
        graph=self.graph({'entry':'def leaf(item): return item\ndef outer(unknown):\n'
                          '    value={}\n    leaf(value)\n    return unknown\na=outer(missing)\n'})
        root=self.expanded_contexts(graph,'outer')[0]
        self.assertEqual(root['status'],'conditional_body_unknown_entry')
        self.assertFalse(any(r['name']=='unknown' for r in root['reads']))
        self.assertEqual(self.call_contexts(graph,'outer')[0]['reads'],[])
        closure=graph['call_context_closure'];edge=next(e for e in closure['edges'] if e['parent_context']==root['id'])
        self.assertEqual(closure['contexts'][edge['child_context']]['reads'][0]['output_types'],['dict'])

    def test_context_closure_invalid_expanded_and_suspended_calls_stay_unresolved(self):
        graph=self.graph({'entry':'def leaf(x): return x\ndef outer(value): return leaf(value)\n'
                          'def gen(value): yield leaf(value)\nasync def coro(value): return leaf(value)\n'
                          'a=outer()\nb=outer(*unknown)\nc=gen({})\nd=coro([])\n'})
        closure=graph['call_context_closure']
        for name in ('outer','gen','coro'):
            for row in self.expanded_contexts(graph,name):
                self.assertIn(row['status'],('argument_binding_unresolved','suspended_body_unresolved'))
                self.assertEqual(row['reads'],[])
                self.assertFalse(any(e['parent_context']==row['id'] for e in closure['edges']))

    def test_context_closure_default_conditions_reach_deep_helper(self):
        graph=self.graph({'entry':'def leaf(x): return x\ndef middle(y): return leaf(y)\n'
                          'def outer(value={}): return middle(value)\na=outer()\n'})
        rows=[r for r in self.expanded_contexts(graph,'leaf') if r['input_facts'][0]['value_facts']==['type:dict']]
        self.assertEqual(len(rows),1)
        self.assertTrue(any(p.startswith('authentic_default_binding:') for p in self.expanded_conditions(graph,rows[0])))

    def test_context_closure_loop_exit_does_not_invent_typed_helper_input(self):
        graph=self.graph({'entry':'def leaf(x): return x\ndef outer(value):\n'
                          '    for step in unknown: value=unknown\n    return leaf(value)\na=outer({})\n'})
        self.assertTrue(all(r['input_facts'][0]['value_facts']==[] for r in self.expanded_contexts(graph,'leaf')))

    def test_context_closure_keeps_unknown_effects_and_nonreference_provenance(self):
        graph=self.graph({'entry':'def leaf(x):\n    unknown()\n    return len(x)\n'
                          'def outer(value): return leaf(value)\na=outer({})\n'})
        closure=graph['call_context_closure']
        self.assertFalse(closure['body_effects_accepted']);self.assertFalse(closure['shared_parameter_facts_changed'])
        self.assertTrue(all(r['other_call_nodes'] for r in self.expanded_contexts(graph,'leaf')))
        self.assertTrue(all(e['reference'] is False for e in graph['edges'] if e['kind']=='expanded_call_context_read_control'))
        self.assertFalse(any(e['operation']=='builtins.len' for e in graph['primitive_effects']))
        self.assertFalse(graph['source_audit_complete'])

    def test_context_closure_empty_module_and_deterministic_condition_order(self):
        empty=self.graph({'entry':'value=1\n'})['call_context_closure']
        self.assertEqual(empty['contexts'],[]);self.assertEqual(empty['condition_sets'],[])
        source={'entry':'def a(x): return b(x)\ndef b(y): return a(y)\nr=a({})\n'}
        self.assertEqual(self.graph(source)['call_context_closure'],self.graph(source)['call_context_closure'])

    def test_call_context_keeps_distinct_entry_types_without_global_narrowing(self):
        graph=self.graph({'entry':'def choose(value): return value\na=choose({})\nb=choose([])\n'})
        rows=self.call_contexts(graph,'choose')
        self.assertEqual([r['reads'][0]['output_types'] for r in rows],[['dict'],['list']])
        self.assertTrue(all(r['contract']=='python_call_context_types.v1' for r in rows))
        self.assertTrue(all(not r['execution_proven'] and not r['shared_parameter_facts_changed'] for r in rows))
        self.assertFalse(any('::choose@' in r['function'] for r in graph['function_return_facts']))

    def test_call_context_unknown_and_invalid_callers_keep_no_body_facts(self):
        graph=self.graph({'entry':'def choose(value): return value\na=choose(unknown)\nb=choose()\nc=choose(*other)\n'})
        rows=self.call_contexts(graph,'choose')
        self.assertEqual([r['status'] for r in rows],['no_exact_entry_types','argument_binding_unresolved','argument_binding_unresolved'])
        self.assertTrue(all(r['reads']==[] and r['nested_call_bindings']==[] for r in rows))

    def test_call_context_passes_copied_parameter_to_actual_helper_binding(self):
        graph=self.graph({'entry':'def helper(item): return item\ndef choose(value):\n'
                          '    copied=value\n    return helper(copied)\na=choose({})\nb=choose([])\n'})
        rows=self.call_contexts(graph,'choose')
        for row,expected in zip(rows,(['type:dict'],['type:list'])):
            child=row['nested_call_bindings'][0];formal=child['formal_bindings'][0]
            self.assertEqual(formal['value_facts'],expected)
            self.assertEqual(child['refined_formals'],['item'])
            self.assertFalse(child['body_context_expanded'])
            self.assertTrue(set(row['preconditions'])<=set(child['preconditions']))
            self.assertTrue(any(p.startswith('call_context_parameter_binding_stable:') for p in formal['preconditions']))
        self.assertEqual(self.call_bindings(graph,'helper')[0]['formal_bindings'][0]['value_facts'],[])

    def test_call_context_join_requires_all_normal_alternatives(self):
        graph=self.graph({'entry':'def choose(value,flag):\n'
                          '    if flag: value=[]\n    return value\n'
                          'def unknown_join(value,flag):\n    if flag: value=unknown\n    return value\n'
                          'a=choose({},True)\nb=unknown_join({},True)\n'})
        row=self.call_contexts(graph,'choose')[0]
        self.assertEqual([r['output_types'] for r in row['reads'] if r['name']=='value'],[['dict','list']])
        self.assertFalse(any(r['name']=='value' for r in self.call_contexts(graph,'unknown_join')[0]['reads']))

    def test_call_context_rebinding_delete_augassign_and_walrus_kill_entry_fact(self):
        for statement in ('value=unknown','del value','value+=unknown','(value:=unknown)'):
            with self.subTest(statement=statement):
                graph=self.graph({'entry':'def choose(value):\n    '+statement+'\n    return value\na=choose({})\n'})
                self.assertFalse(any(r['name']=='value' and graph['nodes'][r['node']]['line']==3
                                     for r in self.call_contexts(graph,'choose')[0]['reads']))

    def test_call_context_local_copy_retains_original_argument_after_rebind(self):
        graph=self.graph({'entry':'def choose(value):\n    copied=value\n    value=[]\n    return copied,value\na=choose({})\n'})
        row=self.call_contexts(graph,'choose')[0]
        final={r['name']:r for r in row['reads'] if graph['nodes'][r['node']]['line']==4}
        self.assertEqual(final['copied']['output_types'],['dict']);self.assertEqual(final['value']['output_types'],['list'])
        self.assertTrue(set(row['entry_bindings'][0]['inputs'])<=set(final['copied']['inputs']))

    def test_call_context_exception_loop_and_context_exits_do_not_borrow_entry(self):
        for body in ('try:\n        value=unknown\n    except Exception:\n        return value',
                     'for item in unknown:\n        pass\n    return value',
                     'with unknown:\n        pass\n    return value'):
            with self.subTest(body=body):
                graph=self.graph({'entry':'def choose(value):\n    '+body+'\na=choose({})\n'})
                self.assertFalse(any(r['name']=='value' for r in self.call_contexts(graph,'choose')[0]['reads']))

    def test_call_context_suspended_bodies_remain_unresolved(self):
        graph=self.graph({'entry':'def gen(value): yield value\nasync def coro(value): return value\na=gen({})\nb=coro([])\n'})
        for name in ('gen','coro'):
            row=self.call_contexts(graph,name)[0]
            self.assertEqual(row['status'],'suspended_body_unresolved');self.assertEqual(row['reads'],[])

    def test_call_context_packs_and_defaults_keep_binding_conditions(self):
        graph=self.graph({'entry':'def choose(value={},*args,**kwargs): return value,args,kwargs\na=choose()\n'})
        row=self.call_contexts(graph,'choose')[0]
        self.assertEqual({r['name']:r['output_types'] for r in row['reads']},
                         {'value':['dict'],'args':['tuple'],'kwargs':['dict']})
        self.assertTrue(any(p.startswith('authentic_default_binding:') for p in row['preconditions']))
        self.assertTrue(all(set(row['preconditions'])<=set(r['preconditions']) for r in row['reads']))

    def test_call_context_opaque_mutation_stays_a_required_condition(self):
        source=('def choose(value,mutate):\n    mutate()\n    return value\na=choose({},unknown)\n')
        graph=self.graph({'entry':source});row=self.call_contexts(graph,'choose')[0]
        self.assertEqual(row['reads'][0]['output_types'],['dict'])
        self.assertTrue(any(p.startswith('call_context_parameter_binding_stable:') for p in row['reads'][0]['preconditions']))
        self.assertFalse(row['body_effects_accepted']);self.assertTrue(row['other_call_nodes'])
        self.assertTrue(any(r['node']==row['node'] and r['reason']=='call_context_body_effects_summary_required' for r in graph['unclassified']))

    def test_call_context_callable_argument_does_not_become_a_builtin_type(self):
        graph=self.graph({'entry':'import os\ndef choose(value): return value\na=choose(os.getpid)\n'})
        row=self.call_contexts(graph,'choose')[0]
        self.assertEqual(row['status'],'no_exact_entry_types');self.assertEqual(row['entry_bindings'],[])

    def test_call_context_control_edges_never_change_reference_or_effect_authority(self):
        graph=self.graph({'entry':'def choose(value): return len(value)\na=choose({})\n'})
        row=self.call_contexts(graph,'choose')[0];read=row['reads'][0]
        edges=[e for e in graph['edges'] if e['kind']=='call_context_read_control' and e['target']==read['node']]
        self.assertTrue(edges);self.assertTrue(all(e['reference'] is False for e in edges))
        self.assertTrue(set(read['inputs'])<={e['source'] for e in edges})
        self.assertFalse(graph['source_audit_complete'])
        self.assertFalse(any(e['operation']=='builtins.len' for e in graph['primitive_effects']))

    def test_successful_local_assignment_selects_branch_producer_at_the_call(self):
        graph=self.graph({'entry':'def consume(value): return value\ndef choose(flag,unknown):\n'
                          '    if flag:\n        value=unknown\n    else:\n        value={}\n        consume(value)\n'})
        binding=self.call_bindings(graph,'consume')[0]
        self.assertEqual(binding['formal_bindings'][0]['value_facts'],['type:dict'])
        rows=self.local_types(graph,'value','choose')
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['output_types'],['dict'])
        self.assertTrue(rows[0]['assignment_nodes'])
        self.assertEqual(rows[0]['contract'],'python_successful_local_type.v1')
        self.assertTrue(any(p.startswith('successful_local_assignment_binding_stable:') for p in rows[0]['preconditions']))
        self.assertFalse(any('::consume@' in row['function'] for row in graph['function_return_facts']))

    def test_successful_local_assignment_requires_every_join_alternative(self):
        for other,expected in [('[]',['dict','list']),('unknown',None)]:
            graph=self.graph({'entry':'def choose(flag,unknown):\n    if flag:\n        value={}\n'
                              '    else:\n        value='+other+'\n    return value\n'})
            rows=self.local_types(graph,'value','choose')
            self.assertEqual(rows[0]['output_types'] if rows else None,expected)
            if expected is not None:self.assertEqual(len(rows[0]['assignment_nodes']),2)

    def test_successful_local_assignment_does_not_include_a_terminated_branch(self):
        graph=self.graph({'entry':'def choose(flag,unknown):\n    if flag:\n        value=unknown\n'
                          '        raise ValueError()\n    else:\n        value={}\n    return value\n'})
        self.assertEqual(self.local_types(graph,'value','choose')[0]['output_types'],['dict'])
        returned=next(r for r in graph['function_return_facts'] if '::choose@' in r['function'])
        self.assertEqual(returned['output_types'],['dict'])

    def test_successful_local_assignment_unknown_rebinding_delete_and_augassign_kill(self):
        for middle in ('value=unknown','del value','value+=unknown','(value:=unknown)'):
            source='def choose(unknown):\n    value={}\n    '+middle+'\n    return value\n'
            graph=self.graph({'entry':source})
            rows=[r for r in self.local_types(graph,'value','choose') if graph['nodes'][r['node']]['line']==4]
            self.assertEqual(rows,[])

    def test_successful_local_assignment_copies_the_active_local_value(self):
        graph=self.graph({'entry':'def choose(flag,unknown):\n    if flag:\n        value=unknown\n        return None\n'
                          '    value={}\n    copied=value\n    value=[]\n    return copied\n'})
        copied=self.local_types(graph,'copied','choose')[0]
        self.assertEqual(copied['output_types'],['dict'])
        self.assertEqual(len(copied['assignment_nodes']),2)
        self.assertTrue(any(p.endswith(':value') for p in copied['preconditions']))
        self.assertTrue(any(p.endswith(':copied') for p in copied['preconditions']))

    def test_successful_local_assignment_does_not_lend_try_state_to_handlers_or_finally(self):
        for tail in ('    except ValueError:\n        return value\n',
                     '    finally:\n        return value\n'):
            graph=self.graph({'entry':'def choose(unknown):\n    value=unknown\n    try:\n'
                              '        value={}\n        may_fail()\n        return value\n'+tail})
            rows=self.local_types(graph,'value','choose')
            self.assertTrue(any(graph['nodes'][r['node']]['line']==6 for r in rows))
            self.assertFalse(any(graph['nodes'][r['node']]['line']==8 for r in rows))

    def test_successful_local_assignment_loop_and_context_exits_keep_uncertainty(self):
        for statement in ('for item in unknown:', 'while unknown:', 'with unknown:'):
            graph=self.graph({'entry':'def choose(unknown):\n    '+statement+'\n        value={}\n'
                              '        consume(value)\n    return value\n'})
            rows=self.local_types(graph,'value','choose')
            self.assertTrue(any(graph['nodes'][r['node']]['line']==4 for r in rows))
            self.assertFalse(any(graph['nodes'][r['node']]['line']==5 for r in rows))

    def test_successful_local_assignment_excludes_nonlocal_global_and_unpack_transfer(self):
        sources=[('value=None\ndef choose():\n    global value\n    value={}\n    return value\n','choose'),
                 ('def outer():\n    value=None\n    def choose():\n        nonlocal value\n        value={}\n        return value\n','outer.choose'),
                 ('def choose(unknown):\n    value,other=unknown\n    return value\n','choose')]
        for source,function in sources:
            graph=self.graph({'entry':source});self.assertEqual(self.local_types(graph,'value',function),[])

    def test_successful_local_assignment_keeps_opaque_nonlocal_mutation_as_a_condition(self):
        source=('def choose():\n    def change():\n        nonlocal value\n        value=[]\n'
                '    value={}\n    change()\n    return value\n')
        run=subprocess.run([sys.executable,'-B','-c',source+'print(choose())\n'],capture_output=True,text=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(run.stdout.strip(),'[]')
        graph=self.graph({'entry':source});row=self.local_types(graph,'value','choose')[0]
        self.assertEqual(row['output_types'],['dict'])
        self.assertTrue(any(p.startswith('successful_local_assignment_binding_stable:') for p in row['preconditions']))
        self.assertTrue(any(r['reason']=='successful_local_assignment_bindings_summary_required' for r in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])

    def test_successful_local_assignment_preserves_native_and_guard_producer_conditions(self):
        graph=self.graph({'entry':'import json\ndef require(c):\n    if not c: raise ValueError()\n'
                          'def parse(raw):\n    value=json.loads(raw)\n    require(type(value) is dict)\n    return value\n'
                          'def choose(raw,flag,unknown):\n    if flag:\n        selected=unknown\n        return None\n'
                          '    selected=parse(raw)\n    return selected\n'})
        row=self.local_types(graph,'selected','choose')[0]
        self.assertEqual(row['output_types'],['dict'])
        for prefix in ('authentic_stdlib_binding:json','authentic_guard_callable_body:','successful_local_assignment_binding_stable:'):
            self.assertTrue(any(p.startswith(prefix) for p in row['preconditions']),prefix)

    def test_successful_local_assignment_disambiguates_nested_call_producers(self):
        graph=self.graph({'entry':'def choose():\n    value=list().append(1)\n    return value\n'})
        row=self.local_types(graph,'value','choose')[0]
        self.assertEqual(row['output_types'],['NoneType'])
        producers=[graph['nodes'][n] for n in row['inputs']]
        self.assertTrue(any(n['kind']=='Call' and n['label']=='list().append(1)' for n in producers))
        self.assertFalse(any(n['kind']=='Call' and n['label']=='list()' for n in producers))

    def test_successful_local_assignment_converges_through_multiple_local_returns(self):
        graph=self.graph({'entry':'def make(flag,unknown):\n    if flag:\n        value=unknown\n        raise ValueError()\n'
                          '    value={}\n    return value\ndef copy(flag,unknown):\n    value=make(flag,unknown)\n'
                          '    return value\ndef caller(flag,unknown):\n    value=copy(flag,unknown)\n    consume(value)\n'
                          'def consume(value): return value\n'})
        row=self.local_types(graph,'value','caller')[0]
        self.assertEqual(row['output_types'],['dict'])
        self.assertEqual(self.call_bindings(graph,'consume')[0]['formal_bindings'][0]['value_facts'],['type:dict'])

    def test_call_bindings_keep_independent_callers_out_of_shared_parameter_facts(self):
        graph = self.graph({'entry': 'def identity(value):\n    return value\na=identity({})\nb=identity("other")\n'})
        rows = self.call_bindings(graph, 'identity')
        self.assertEqual(len(rows), 2)
        self.assertEqual([r['formal_bindings'][0]['value_facts'] for r in rows], [['type:dict'], ['type:str']])
        self.assertEqual(len({r['formal_bindings'][0]['parameter_node'] for r in rows}), 1)
        self.assertFalse(any('::identity@' in r['function'] for r in graph['function_return_facts']))
        for row in rows:
            self.assertEqual(row['status'], 'conditionally_bound')
            self.assertFalse(row['execution_proven'])
            self.assertFalse(row['shared_parameter_facts_changed'])
            self.assertEqual(row['contract'], 'python_call_argument_binding.v1')

    def test_call_bindings_retain_definition_time_defaults_and_keyword_selection(self):
        graph = self.graph({'entry': 'seed=[]\ndef choose(a, /, b=seed, *, c=None):\n    return a\nchoose({}, c=3)\n'})
        row = self.call_bindings(graph, 'choose')[0]
        a, b, c = row['formal_bindings']
        self.assertEqual((a['kind'], a['selection'], a['value_facts']), ('positional_only', 'positional', ['type:dict']))
        self.assertEqual((b['selection'], b['value_facts']), ('definition_default', ['type:list']))
        self.assertEqual(b['arguments'], [{'node': b['default_node']}])
        self.assertEqual(graph['nodes'][b['default_node']]['function'], '<module>')
        self.assertTrue(any(p.startswith('authentic_default_binding:') for p in b['preconditions']))
        self.assertEqual((c['kind'], c['selection'], c['value_facts']), ('keyword_only', 'keyword', ['type:int']))
        self.assertIsNotNone(c['default_node'])
        self.assertFalse(any(p.endswith(':c') and 'default_binding' in p for p in row['preconditions']))

    def test_call_bindings_pack_variadics_and_keep_positional_only_keyword_in_kwargs(self):
        source='def choose(x, /, *rest, y=False, **extra):\n    return x,rest,y,extra\n'
        graph=self.graph({'entry':source+'choose(1,2,3,x="shadow",z={})\nchoose(1)\n'})
        for row in self.call_bindings(graph, 'choose'):
            self.assertEqual(row['status'], 'conditionally_bound')
            values={r['name']:r for r in row['formal_bindings']}
            self.assertEqual(values['x']['value_facts'], ['type:int'])
            self.assertEqual(values['rest']['value_facts'], ['type:tuple'])
            self.assertEqual(values['extra']['value_facts'], ['type:dict'])
        first,last=self.call_bindings(graph,'choose')
        packed={r['name']:r for r in first['formal_bindings']}
        self.assertEqual([r['position'] for r in packed['rest']['arguments']], [1,2])
        self.assertEqual([r['keyword'] for r in packed['extra']['arguments']], ['x','z'])
        self.assertTrue(all(not r['arguments'] for r in last['formal_bindings'] if r['kind'].startswith('var_')))
        run=subprocess.run([sys.executable,'-B','-c',source+'print(choose(1,2,3,x="shadow",z={}))'],capture_output=True,text=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(run.stdout.strip(), "(1, (2, 3), False, {'x': 'shadow', 'z': {}})")

    def test_call_bindings_invalid_signatures_have_no_parameter_value_facts(self):
        for definition,call,error in (
                ('def f(x): return x', 'f(1,x=2)', 'multiple_values:x'),
                ('def f(x): return x', 'f(1,2)', 'too_many_positional_arguments'),
                ('def f(x,/,y=None): return x', 'f(x=1)', 'positional_only_keyword:x'),
                ('def f(*,x): return x', 'f()', 'missing_argument:x'),
                ('def f(x): return x', 'f(1,unknown=2)', 'unexpected_keyword:unknown')):
            with self.subTest(call=call):
                graph=self.graph({'entry':definition+'\n'+call+'\n'})
                row=self.call_bindings(graph,'f')[0]
                self.assertEqual(row['status'],'invalid_static_binding')
                self.assertIn(error,row['errors'])
                self.assertTrue(all(not f['value_facts'] for f in row['formal_bindings']))
                run=subprocess.run([sys.executable,'-B','-c',definition+'\ntry:\n    '+call+'\nexcept TypeError:\n    print("binding rejected")'],capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stderr)
                self.assertEqual(run.stdout.strip(),'binding rejected')

    def test_call_bindings_expansions_preserve_projected_inputs_without_accepting_protocols(self):
        graph=self.graph({'entry':'import os\ndef f(x,*rest,**kw): return x\nvalues=[os.getpid]\nf(*values,**mapping)\n'})
        row=self.call_bindings(graph,'f')[0]
        self.assertEqual(row['status'],'expanded_binding_unresolved')
        self.assertEqual(graph['nodes'][row['positional_arguments'][0]['node']]['kind'],'expanded_positional_value')
        self.assertIsNone(row['keyword_arguments'][0]['name'])
        self.assertIsNotNone(row['keyword_arguments'][0]['key_node'])
        self.assertTrue(all(f['selection']=='unresolved' and not f['value_facts'] for f in row['formal_bindings']))
        self.assertTrue(any(p.startswith('expanded_argument_protocols_and_binding:') for p in row['preconditions']))
        self.assertTrue(self.reachable(graph,self.nodes(graph,'Attribute','os.getpid'),self.nodes(graph,'symbol','x','f')))

    def test_call_bindings_distinguish_methods_staticmethods_and_constructor_returns(self):
        graph=self.graph({'entry':'class C:\n    def __init__(self,x): self.x=x\n'
                          '    def f(self,y): return y\n    @staticmethod\n    def s(z): return z\n'
                          'c=C(1)\nc.f({})\nc.s("value")\n'})
        init=self.call_bindings(graph,'C.__init__')[0]
        method=self.call_bindings(graph,'C.f')[0]
        static=self.call_bindings(graph,'C.s')[0]
        self.assertFalse(init['returns_to_call'])
        self.assertTrue(method['returns_to_call'])
        for row in (init,method):
            self.assertIsNotNone(row['bound_receiver_node'])
            self.assertEqual(row['formal_bindings'][0]['selection'],'bound_receiver')
            self.assertEqual(row['formal_bindings'][0]['arguments'][0]['node'],row['bound_receiver_node'])
        self.assertIsNone(static['bound_receiver_node'])
        self.assertEqual(static['formal_bindings'][0]['value_facts'],['type:str'])

    def test_call_bindings_keep_each_possible_declaration_and_its_invalid_alternative(self):
        graph=self.graph({'entry':'def one(x): return x\ndef two(x,y): return y\n'
                          'fn=one\nif unknown: fn=two\nfn({})\n'})
        one=self.call_bindings(graph,'one')[0];two=self.call_bindings(graph,'two')[0]
        self.assertEqual(one['node'],two['node'])
        self.assertEqual(one['status'],'conditionally_bound')
        self.assertEqual(two['status'],'invalid_static_binding')
        self.assertIn('missing_argument:y',two['errors'])
        self.assertIn('selected_call_target:'+one['function'],one['preconditions'])
        self.assertFalse(one['execution_proven'])

    def test_call_bindings_default_replacement_remains_an_explicit_runtime_obligation(self):
        source='def f(value={}): return value\nf.__defaults__=([],)\nprint(type(f()).__name__)\n'
        run=subprocess.run([sys.executable,'-B','-c',source],capture_output=True,text=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(run.stdout.strip(),'list')
        graph=self.graph({'entry':source});row=self.call_bindings(graph,'f')[0]
        self.assertEqual(row['formal_bindings'][0]['value_facts'],['type:dict'])
        self.assertTrue(any(p.startswith('authentic_default_binding:') for p in row['preconditions']))
        self.assertTrue(any(p.startswith('default_binding_stable_during_call:') for p in row['preconditions']))
        self.assertFalse(row['execution_proven']);self.assertFalse(graph['source_audit_complete'])

    def test_call_bindings_signature_replacement_does_not_prove_dispatch(self):
        source='def f(x): return x\ndef replacement(x,y): return y\nf.__code__=replacement.__code__\n'
        graph=self.graph({'entry':source+'f(1)\n'});row=self.call_bindings(graph,'f')[0]
        self.assertEqual(row['status'],'conditionally_bound')
        self.assertIn('authentic_callable_signature:'+row['function'],row['preconditions'])
        self.assertIn('callable_signature_stable_during_call:'+row['function'],row['preconditions'])
        run=subprocess.run([sys.executable,'-B','-c',source+'try:\n    f(1)\nexcept TypeError:\n    print("changed signature")'],capture_output=True,text=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(run.stdout.strip(),'changed signature')
        self.assertFalse(row['execution_proven'])

    def test_call_bindings_carry_successful_parser_conditions_into_exact_actual_arguments(self):
        graph=self.graph({'entry':'import json\ndef require(c):\n    if not c: raise ValueError()\n'
                          'def parse(raw):\n    value=json.loads(raw)\n    require(type(value) is dict)\n    return value\n'
                          'def admit(record,q,*,receipt): return q\nadmit(parse("{}"),parse("{}"),receipt=parse("{}"))\n'})
        row=self.call_bindings(graph,'admit')[0]
        self.assertEqual(row['status'],'conditionally_bound')
        self.assertEqual([f['value_facts'] for f in row['formal_bindings']],[['type:dict']]*3)
        for formal in row['formal_bindings']:
            self.assertIn('authentic_builtin_binding:type',formal['preconditions'])
            self.assertTrue(any(p.startswith('authentic_guard_callable_body:') for p in formal['preconditions']))
        self.assertFalse(any('::admit@' in r['function'] for r in graph['function_return_facts']))

    def test_call_bindings_nested_defaults_do_not_borrow_a_single_outer_callers_type(self):
        graph=self.graph({'entry':'def outer(value):\n    def inner(item=value): return item\n    return inner()\n'
                          'outer({})\nouter("different")\n'})
        row=self.call_bindings(graph,'outer.inner')[0]
        formal=row['formal_bindings'][0]
        self.assertEqual(formal['selection'],'definition_default')
        self.assertEqual(formal['value_facts'],[])
        self.assertEqual(graph['nodes'][formal['default_node']]['function'],'outer')
        self.assertFalse(graph['source_audit_complete'])

    def test_call_bindings_are_deterministic_across_source_mapping_order(self):
        sources={'helper':'def f(x,*,y=None): return x\n','entry':'from helper import f\nf({},y=1)\nf("x")\n'}
        first=self.graph(sources);second=self.graph(dict(reversed(list(sources.items()))))
        self.assertEqual(first['call_argument_binding_inventory'],second['call_argument_binding_inventory'])
        self.assertEqual(len(self.call_bindings(first,'f')),2)

    def test_mapping_constructor_does_not_accept_unknown_mapping_protocol(self):
        graph = self.graph({'entry': 'def copy(unknown):\n    return dict(unknown)\n'})
        self.assertTrue(any(row['reason'] == 'mapping_update_source_summary_required' for row in graph['unclassified']))
        self.assertFalse(graph['source_audit_complete'])


class ReleaseBootstrapTests(unittest.TestCase):
    """Closed byte-graph fixtures test authentication only, never live acceptance."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as bootstrap
        sys.path[:] = previous
        self.bootstrap = bootstrap
        self.policy = json.loads(CONTRACT_PATH.read_bytes())
        self.temporary = tempfile.TemporaryDirectory(prefix="city-byte-bootstrap-", dir="/private/tmp")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "release"
        # An explicitly supplied fresh artifact path has no required basename.
        self.artifacts = Path(self.temporary.name) / "independent-captures"
        self.root.mkdir(); self.artifacts.mkdir()
        self.prefix = self.policy["runtime"]["output_root"] + "/"
        for name in self.policy["release_members"]:
            if name.startswith(self.prefix):
                continue
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True)
            source = CONTRACT_PATH.parent.parent / name
            path.write_bytes(source.read_bytes() if source.is_file() else b"nonexecuted byte-inventory fixture\n")
        for name in self.policy["artifact_relative_paths"]:
            path = self.artifacts / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"byte-graph fixture; not live process evidence\n")
        for symbol in ("R0", "R1", "QA", "QB"):
            original = CONTRACT_PATH.parent / "ConcurrentExternalEvidenceArbitrationProofRecords" / ("concurrent_external_" + symbol + ".json")
            (self.artifacts / "canonical" / (symbol + ".json")).write_bytes(original.read_bytes())
        definitions = self.policy["wire_schemas"]
        self.build = schema_example(definitions["build_record"], definitions)
        self.acquisition = schema_example(definitions["acquisition_record"], definitions)
        self.cases = {name: schema_example(definitions["case_record"], definitions)
                      for name in self.policy["artifact_hash_graph"]["case_ids"]}
        self.refresh_graph()

    def index(self, name):
        raw = (self.artifacts / name).read_bytes()
        return {"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}

    def refresh_manifest(self):
        lines = []
        for name in sorted(self.policy["release_members"]):
            path = (self.artifacts / name[len(self.prefix):] if name.startswith(self.prefix) else self.root / name)
            lines.append(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + name + "\n")
        (self.root / self.policy["release_manifest"]).write_text("".join(lines), encoding="ascii")

    def refresh_graph(self):
        graph = self.policy["artifact_hash_graph"]
        for name, record in self.cases.items():
            record["witness_id"] = name
            record["artifact_sha256"] = [self.index(path) for path in graph["case_record_targets"][name]]
            (self.artifacts / name / "record.json").write_bytes(stored_json_bytes(record))
        self.build["log"] = self.index("build.log")
        (self.artifacts / "build.json").write_bytes(stored_json_bytes(self.build))
        self.acquisition["artifact_members"] = self.policy["artifact_relative_paths"]
        self.acquisition["artifact_hashes"] = [self.index(name) for name in graph["acquisition_targets"]]
        self.acquisition["cases"] = [{"witness_id": name, "record_path": name + "/record.json",
                                       "record_sha256": self.index(name + "/record.json")["sha256"]}
                                      for name in graph["case_ids"]]
        self.acquisition["build_sha256"] = self.index("build.json")["sha256"]
        (self.artifacts / "acquisition.json").write_bytes(stored_json_bytes(self.acquisition))
        self.refresh_manifest()

    def test_complete_byte_graph_and_arbitrary_safe_artifact_path(self):
        context = self.bootstrap.authenticate_release(self.root, self.artifacts)
        self.assertEqual(len(context["artifacts"]), 219)
        self.assertEqual(len(context["source_bytes"]), 70)
        self.assertEqual(len(context["members"]), 289)
        self.assertNotIn("accepted", context)

    def test_modified_stream_rejects_with_stale_manifest_and_with_rehashed_manifest(self):
        path = self.artifacts / "W1/domain_A.stdout.log"
        self.assertTrue(path.is_file())
        path.write_bytes(path.read_bytes() + b"changed\n")
        for rehash in (False, True):
            if rehash:
                self.refresh_manifest()
            with self.subTest(rehashed_manifest=rehash):
                with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
                    self.bootstrap.authenticate_release(self.root, self.artifacts)

    def test_pinned_canonical_bytes_reject_even_after_graph_rehash(self):
        path = self.artifacts / "canonical/R0.json"; path.write_bytes(path.read_bytes()[:-1])
        self.refresh_graph()
        with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
            self.bootstrap.authenticate_release(self.root, self.artifacts)

    def test_manifest_closed_set_order_and_duplicates(self):
        path = self.root / self.policy["release_manifest"]; original = path.read_bytes()
        lines = original.splitlines(keepends=True)
        for raw in [b"".join(reversed(lines)), b"".join(lines[:-1]), original + lines[0],
                    lines[0] + b"".join(lines[:-1]), original.replace(b"  ", b" ", 1)]:
            path.write_bytes(raw)
            with self.subTest(manifest_sha256=hashlib.sha256(raw).hexdigest()):
                with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
                    self.bootstrap.authenticate_release(self.root, self.artifacts)

    def test_unlisted_artifact_and_alias_reject(self):
        path = self.artifacts / "undeclared"; path.write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
            self.bootstrap.authenticate_release(self.root, self.artifacts)
        path.unlink()
        path = self.artifacts / "build.log"; raw = path.read_bytes(); path.unlink()
        target = Path(self.temporary.name) / "alias-target"; target.write_bytes(raw); path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
            self.bootstrap.authenticate_release(self.root, self.artifacts)

    def child_import(self):
        code = ("import sys; sys.path.insert(0, sys.argv[1] + '/proof_kernel'); "
                "import verify_live_cross_domain_evidence_round_trip_release as v; "
                "v.authenticated_imports(sys.argv[1], sys.argv[2]); print('authenticated_imports_only')")
        return subprocess.run([sys.executable, "-B", "-c", code, str(self.root), str(self.artifacts)],
                              capture_output=True, text=True, timeout=10, cwd=str(self.root))

    def test_valid_bootstrap_reaches_authenticated_local_imports(self):
        result = self.child_import()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "authenticated_imports_only\n")

    def test_dependency_inventory_follows_local_imports_without_execution(self):
        context = self.bootstrap.authenticate_release(self.root, self.artifacts)
        inventory = self.bootstrap.python_dependency_inventory(context['source_bytes'], stdlib_top_level_names())
        self.assertEqual(len(inventory['files']), 6)
        functions = {(row['path'], row['function']) for row in inventory['functions']}
        self.assertIn(('proof_kernel/live_cross_domain_evidence_round_trip_harness.py',
                       'MacProcessObserver.exclusive_pipe_holders.observe'), functions)
        self.assertTrue(any(row['local_path'] == 'proof_kernel/kernel.py' for row in inventory['imports']))
        self.assertTrue(all(row['local_path'] is None or row['local_path'] in context['source_bytes']
                            for row in inventory['imports']))

    def test_executable_aliases_report_the_actual_source_and_function(self):
        relative = 'proof_kernel/live_cross_domain_evidence_round_trip.py'
        mutations = [
            (b'def entry():\n    alias = eval\n    return alias("1")\n', 'entry', 'eval', 2),
            (b'def entry():\n    def helper():\n        return __import__\n    return helper()("os")\n',
             'entry.helper', '__import__', 3),
            (b'import importlib as hidden\ndef entry():\n    return hidden.import_module("os")\n',
             '<module>', 'importlib', 1),
            (b'def entry(value):\n    return value.__globals__\n', 'entry', '__globals__', 2),
            (b'def entry(value):\n    return getattr(value, "__import__")\n', 'entry', 'getattr.__import__', 2),
        ]
        for raw, function, callee, line in mutations:
            with self.subTest(callee=callee):
                (self.root / relative).write_bytes(raw)
                self.refresh_manifest()
                context = self.bootstrap.authenticate_release(self.root, self.artifacts)
                with self.assertRaises(self.bootstrap.SourceInputForbidden) as failure:
                    self.bootstrap.python_dependency_inventory(context['source_bytes'], stdlib_top_level_names())
                self.assertEqual(str(failure.exception), 'lcer.source_input_forbidden')
                self.assertEqual(failure.exception.edge, {'path': relative, 'function': function,
                                  'input': 'platform', 'callee': callee, 'line': line})

    def test_unlisted_local_import_rejects_after_candidate_manifest_rehash(self):
        path = self.root / 'proof_kernel/live_cross_domain_evidence_round_trip.py'
        path.write_bytes(b'def entry():\n    import unlisted_city_module\n')
        self.refresh_manifest()
        context = self.bootstrap.authenticate_release(self.root, self.artifacts)
        with self.assertRaises(self.bootstrap.SourceInputForbidden) as failure:
            self.bootstrap.python_dependency_inventory(context['source_bytes'], stdlib_top_level_names())
        self.assertEqual(failure.exception.edge, {'path': path.relative_to(self.root).as_posix(),
                          'function': 'entry', 'input': 'platform', 'callee': 'unlisted_city_module', 'line': 2})
        result = self.child_import()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('lcer.source_input_forbidden', result.stderr)

    def test_tampered_adjacent_source_never_executes(self):
        path = self.root / "proof_kernel/live_cross_domain_evidence_round_trip.py"
        path.write_bytes(b"raise RuntimeError('UNVERIFIED_SOURCE_EXECUTED')\n")
        result = self.child_import()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("UNVERIFIED_SOURCE_EXECUTED", result.stdout + result.stderr)
        self.assertIn("lcer.release_evidence_invalid", result.stderr)

    def test_stdlib_shadow_never_executes(self):
        path = self.root / "proof_kernel/json.py"
        path.write_bytes(b"raise RuntimeError('SHADOW_EXECUTED')\n")
        result = self.child_import()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("SHADOW_EXECUTED", result.stdout + result.stderr)
        self.assertIn("lcer.release_evidence_invalid", result.stderr)

    def test_valid_poisoned_bytecode_never_executes_under_minus_B(self):
        path = self.root / 'proof_kernel/concurrent_external_evidence_arbitration.py'
        original = path.read_bytes()
        path.write_bytes(b"raise RuntimeError('UNVERIFIED_BYTECODE_EXECUTED')\n")
        compile_cache = Path(self.temporary.name) / 'fixture-compiler-cache'
        compiled = subprocess.run([sys.executable, '-B', '-X', 'pycache_prefix=' + str(compile_cache),
                                   '-m', 'py_compile', str(path)],
                                  capture_output=True, text=True, timeout=10)
        self.assertEqual(compiled.returncode, 0, compiled.stderr)
        path.write_bytes(original)
        caches = list(compile_cache.rglob('concurrent_external_evidence_arbitration.*.pyc'))
        self.assertEqual(len(caches), 1)
        raw = caches[0].read_bytes()
        # Use the real interpreter's compiled body and magic. Bind the cache
        # header to the restored, immutable source so ordinary -B imports
        # would regard this different executable body as current.
        header = raw[:4] + struct.pack('<III', 0, int(path.stat().st_mtime) & 0xffffffff, len(original))
        local_cache = path.parent / '__pycache__' / caches[0].name
        local_cache.parent.mkdir()
        local_cache.write_bytes(header + raw[16:])
        self.refresh_manifest()
        result = self.child_import()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('UNVERIFIED_BYTECODE_EXECUTED', result.stdout + result.stderr)
        self.assertIn('lcer.release_evidence_invalid', result.stderr)

    def test_local_package_cannot_replace_an_authenticated_source_module(self):
        package = self.root / 'proof_kernel/kernel'
        package.mkdir()
        (package / '__init__.py').write_bytes(b"raise RuntimeError('UNVERIFIED_PACKAGE_EXECUTED')\n")
        result = self.child_import()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('UNVERIFIED_PACKAGE_EXECUTED', result.stdout + result.stderr)
        self.assertIn('lcer.release_evidence_invalid', result.stderr)

    def test_native_module_substitute_is_rejected_before_local_import(self):
        (self.root / 'proof_kernel/kernel.so').write_bytes(b'undeclared native-module fixture')
        result = self.child_import()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('lcer.release_evidence_invalid', result.stderr)

    def test_normal_acquire_blocks_stdlib_shadow_before_model_import(self):
        (self.root / 'proof_kernel/json.py').write_bytes(b"raise RuntimeError('ACQUIRE_SHADOW_EXECUTED')\n")
        result = subprocess.run([sys.executable, '-B', 'proof_kernel/live_cross_domain_evidence_round_trip_harness.py',
                                 'acquire', '--runtime-parent', str(Path(self.temporary.name) / 'runtime'),
                                 '--output', str(Path(self.temporary.name) / 'output')],
                                cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('ACQUIRE_SHADOW_EXECUTED', result.stdout + result.stderr)
        self.assertIn('lcer.source_input_forbidden', result.stderr)
        self.assertFalse((Path(self.temporary.name) / 'runtime').exists())

    def test_normal_acquire_blocks_local_package_before_model_import(self):
        package = self.root / 'proof_kernel/live_cross_domain_evidence_round_trip'
        package.mkdir()
        (package / '__init__.py').write_bytes(b"raise RuntimeError('ACQUIRE_PACKAGE_EXECUTED')\n")
        result = subprocess.run([sys.executable, '-B', 'proof_kernel/live_cross_domain_evidence_round_trip_harness.py',
                                 'acquire', '--runtime-parent', str(Path(self.temporary.name) / 'runtime'),
                                 '--output', str(Path(self.temporary.name) / 'output')],
                                cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('ACQUIRE_PACKAGE_EXECUTED', result.stdout + result.stderr)
        self.assertIn('lcer.source_input_forbidden', result.stderr)
        self.assertFalse((Path(self.temporary.name) / 'runtime').exists())

    def test_candidate_manifest_cannot_authorize_candidate_import_side_effects(self):
        path = self.root / "proof_kernel/live_cross_domain_evidence_round_trip.py"
        path.write_bytes(b"raise RuntimeError('CANDIDATE_SOURCE_EXECUTED')\n")
        self.refresh_manifest()
        result = self.child_import()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "authenticated_imports_only\n")
        self.assertNotIn("CANDIDATE_SOURCE_EXECUTED", result.stderr)

    def test_immutable_predecessor_rejects_even_after_candidate_manifest_rehash(self):
        path = self.root / "proof_kernel/concurrent_external_evidence_arbitration.py"
        path.write_bytes(b"raise RuntimeError('CHANGED_PREDECESSOR_EXECUTED')\n")
        self.refresh_manifest()
        result = self.child_import()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("CHANGED_PREDECESSOR_EXECUTED", result.stdout + result.stderr)
        self.assertIn("lcer.release_evidence_invalid", result.stderr)

    def test_byte_fixture_is_not_accepted_as_live_release(self):
        result = subprocess.run([sys.executable, "-B", "proof_kernel/verify_live_cross_domain_evidence_round_trip_release.py",
                                 "verify", "--artifacts", str(self.artifacts)],
                                cwd=str(self.root), capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout), {'status': 'fail',
                         'failure_codes': ['lcer.release_evidence_invalid']})

    def test_normal_verifier_rejects_changed_immutable_before_its_import(self):
        sentinel = self.root / 'unverified-predecessor-executed'
        path = self.root / 'proof_kernel/concurrent_external_evidence_arbitration.py'
        path.write_bytes(('from pathlib import Path\nPath(%r).write_text("executed")\n' % str(sentinel)).encode())
        self.refresh_manifest()
        result = subprocess.run([sys.executable, '-B', 'proof_kernel/verify_live_cross_domain_evidence_round_trip_release.py',
                                 'verify', '--artifacts', str(self.artifacts)],
                                cwd=str(self.root), capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout), {'status': 'fail',
                         'failure_codes': ['lcer.release_evidence_invalid']})
        self.assertFalse(sentinel.exists())


class IndependentCanonicalReplayTests(unittest.TestCase):
    """Synthetic captures prove replay calculations only, not physical emission."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        import concurrent_external_evidence_arbitration as canonical
        self.verifier = verifier; self.canonical = canonical
        self.raw = CONTRACT_PATH.read_bytes(); self.policy = json.loads(self.raw)
        self.artifacts = {"canonical/" + symbol + ".json": (CONTRACT_PATH.parent /
            "ConcurrentExternalEvidenceArbitrationProofRecords" / ("concurrent_external_" + symbol + ".json")).read_bytes()
            for symbol in ("R0", "R1", "QA", "QB")}

    def core_case(self, name):
        core = CanonicalRoundTrip(self.raw, name)
        r0 = self.canonical.initial_canonical_envelope()
        case = {"witness_id": name, "captured_evidence": [], "command_trace": []}
        captures = {}
        for domain, symbol in (("domain_A", "QA"), ("domain_B", "QB")):
            q = parse_stored_json(self.artifacts["canonical/" + symbol + ".json"])
            capture = {"q_raw_utf8": stored_json_bytes(q).decode(),
                       "acceptance_receipt_raw_utf8": stored_json_bytes(self.canonical.materialization_acceptance_receipt(r0, domain, "unit_test_" + domain)).decode(),
                       "emission_receipt_raw_utf8": stored_json_bytes(self.canonical.evidence_emission_receipt(r0, q, domain, "unit_test_" + domain)).decode()}
            captures[domain] = capture
            case["captured_evidence"].append({"domain": domain, "emission": capture})
        admitted = {}; constructed = None
        for function, domain in core._sequence:
            if function == "admit_external_input_candidate":
                capture = captures[domain]; q = json.loads(capture["q_raw_utf8"])
                if name == "F03": q["target"]["id"] = "shared_slot_02"
                if name == "F05": q["source"]["source_record_hash"] = self.canonical.canonical_hash(json.loads(self.artifacts["canonical/R1.json"]))
                if name == "F06": q["proposed_effect"]["path"] = "/current_causal_state/forbidden_owner"
                if name in {"F03", "F05", "F06"}:
                    del q["evidence"]["evidence_digest"]
                    q["evidence"]["evidence_digest"] = self.canonical.evidence_digest(q)
                if name == "F10b" and core.publication_count:
                    q["input_id"] = "replay_probe_new_input"
                raw_q = stored_json_bytes(q)
                args = {"schema": "city.live_evidence_admission_arguments.v1", "record_raw_utf8": core.head_raw.decode(),
                        "q_object_raw_utf8": stored_json_bytes(q).decode(),
                        "q_raw_base64": base64.b64encode(raw_q[:-1] if name == "F02" else raw_q).decode(),
                        "materialization_receipt_raw_utf8": capture["acceptance_receipt_raw_utf8"],
                        "emission_receipt_raw_utf8": capture["emission_receipt_raw_utf8"]}
                result, call = core.call(function, args)
                if result is not None: admitted[domain] = result
            elif function == "construct_bext_from_sealed_fixture_set":
                order = next((row["presentation"] for row in self.policy["witnesses"] if row["id"] == name), ["domain_A", "domain_B"])
                if name == "F01": order = ["domain_A"]
                if name == "F04a": order = ["domain_A", "domain_A"]
                members = [copy.deepcopy(admitted[key]) for key in order]
                if name == "F04b": members[1]["physical_event_id"] = members[0]["physical_event_id"]
                args = {"schema": "city.live_evidence_construction_arguments.v1", "record_raw_utf8": core.head_raw.decode(),
                        "fixture_raw_utf8": stored_json_bytes(self.canonical.primary_fixture()).decode(),
                        "presentation_members_raw_utf8": [stored_json_bytes(member).decode() for member in members]}
                constructed, call = core.call(function, args)
            else:
                batch, mapping = constructed
                args = {"schema": "city.live_evidence_resolution_arguments.v1", "record_raw_utf8": core.head_raw.decode(),
                        "bext_raw_utf8": stored_json_bytes(batch).decode(),
                        "admitted_members": [{"input_id": key, "member_raw_utf8": stored_json_bytes(mapping[key]).decode()} for key in sorted(mapping)],
                        "fault_point": self.policy["canonical_faults"][int(name[1:]) - 1] if name.startswith("C") else None}
                _, call = core.call(function, args)
            case["command_trace"].append({"event_id": "canonical_call", "payload": call})
        case["canonical_artifacts"] = {"initial_raw_utf8": self.artifacts["canonical/R0.json"].decode(),
                                       "published_raw_utf8": core.head_raw.decode() if core.publication_count else None,
                                       "terminal_raw_utf8": core.head_raw.decode()}
        return case

    def replay(self, case):
        return self.verifier._replay_canonical(self.policy, self.artifacts, case, self.canonical)

    def test_all_35_actual_core_prefixes_replay_independently(self):
        for name in self.policy["artifact_hash_graph"]["case_ids"]:
            with self.subTest(case=name):
                case = self.core_case(name); result = self.replay(case)
                self.assertEqual(result["call_count"], len(case["command_trace"]))
                self.assertEqual(result["publication_count"], int(case["canonical_artifacts"]["published_raw_utf8"] is not None))

    def test_changed_return_exception_and_publication_reject(self):
        for name, field, value in [("W1", "return_raw_utf8", "{}\n"), ("W1", "published_record_raw_utf8", None),
                                    ("C01", "exception_code", "concurrent_external_batch_resolution_rejected")]:
            case = self.core_case(name); case["command_trace"][-1]["payload"][field] = value
            with self.subTest(case=name, field=field):
                with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
                    self.replay(case)

    def test_duplicate_member_key_and_unlisted_nested_q_reject(self):
        case = self.core_case("W1")
        members = case["command_trace"][-1]["payload"]["arguments"]["admitted_members"]
        members.append(copy.deepcopy(members[0]))
        with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
            self.replay(case)
        case = self.core_case("W1")
        args = case["command_trace"][0]["payload"]["arguments"]
        q = json.loads(args["q_object_raw_utf8"]); q["unlisted"] = True
        args["q_object_raw_utf8"] = stored_json_bytes(q).decode()
        with self.assertRaisesRegex(ValueError, "^lcer.schema_invalid$"):
            self.replay(case)

    def test_call_deletion_and_changed_capture_link_reject(self):
        case = self.core_case("W1"); case["command_trace"].pop(0)
        with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
            self.replay(case)
        case = self.core_case("W1")
        case["captured_evidence"][0]["emission"]["acceptance_receipt_raw_utf8"] = "{}\n"
        with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
            self.replay(case)


class TraceRelationTests(unittest.TestCase):
    """Synthetic wire bytes test transport relations, not process or case success."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier; self.policy = json.loads(CONTRACT_PATH.read_bytes())
        self.definitions = self.policy["wire_schemas"]
        self.artifacts = {}; self.events = []
        self.case = {"witness_id": "W1", "process_bindings": [], "command_trace": self.events,
                     "liveness_checkpoints": [], "head_dispositions": [], "live_observations": [],
                     "materialization_receipts": [], "captured_evidence": []}
        for domain in ("domain_A", "domain_B"):
            binding = schema_example(self.definitions["process_binding"], self.definitions)
            binding.update(witness_id="W1", domain=domain, launch_id="offline_" + domain)
            self.case["process_bindings"].append(binding)
            self.case["captured_evidence"].append({"domain": domain, "emission": None})
            stream = b"LogFixture: offline byte relation only\n"; stdin_offset = 0
            startup = schema_example(self.definitions["startup"], self.definitions)
            startup.update(witness_id="W1", domain=domain, launch_id=binding["launch_id"])
            self.add_wire("stdout", "startup", startup, len(stream)); stream += stored_json_bytes(startup)
            for operation, command, argument, response_type in [
                ("bind_0001", "bind", binding, "bind_ack"), ("shutdown_0001", "shutdown", None, "shutdown_ack")]:
                request = {"schema": "city.live_evidence_command.v1", "witness_id": "W1", "domain": domain,
                           "launch_id": binding["launch_id"], "operation_id": operation,
                           "binding_sha256": hashlib.sha256(stored_json_bytes(binding)).hexdigest(), "command": command, "payload": argument}
                self.add_wire("stdin", "command", request, stdin_offset); stdin_offset += len(stored_json_bytes(request))
                response = dict(request, schema="city.live_evidence_response.v1", status="ok", error=None,
                                payload=schema_example(self.definitions[response_type], self.definitions))
                self.add_wire("stdout", "response", response, len(stream)); stream += stored_json_bytes(response)
            self.artifacts["W1/" + domain + ".stdout.log"] = stream
            self.artifacts["W1/" + domain + ".stderr.log"] = b"offline fixture stderr\n"
        self.rechain()

    def add_wire(self, direction, schema, message, offset):
        self.events.append({"sequence": len(self.events), "event_id": "wire_event", "operation_id": message.get("operation_id"),
                            "domain": message["domain"], "monotonic_ns": len(self.events),
                            "payload": {"direction": direction, "raw_line_utf8": stored_json_bytes(message).decode(),
                                        "stream_byte_offset": offset, "parsed_schema": schema}, "previous_event_sha256": None})

    def rechain(self):
        raw_lines = []; previous = None
        for index, event in enumerate(self.events):
            event["sequence"] = index; event["previous_event_sha256"] = previous
            raw = stored_json_bytes(event); raw_lines.append(raw); previous = hashlib.sha256(raw).hexdigest()
        self.artifacts["W1/harness.jsonl"] = b"".join(raw_lines)

    def check(self):
        return self.verifier._trace_relations(self.policy, self.artifacts, self.case)

    def test_original_byte_offsets_and_response_pairs(self):
        result = self.check()
        self.assertEqual(len(result["commands"]), 4)
        self.assertEqual(len(result["responses"]), 4)
        self.assertEqual(len(result["startups"]), 2)

    def test_wrong_response_command_or_operation_rejects_after_rehash(self):
        event = self.events[2]; original = copy.deepcopy(event)
        stream = self.artifacts["W1/domain_A.stdout.log"]
        for field, value in [("command", "emit"), ("operation_id", "emit_0001")]:
            self.events[2] = copy.deepcopy(original); event = self.events[2]
            message = json.loads(event["payload"]["raw_line_utf8"]); old = event["payload"]["raw_line_utf8"].encode()
            message[field] = value; raw = stored_json_bytes(message)
            event["payload"]["raw_line_utf8"] = raw.decode()
            if field == "operation_id": event["operation_id"] = value
            self.artifacts["W1/domain_A.stdout.log"] = stream.replace(old, raw)
            self.rechain()
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
                    self.check()

    def test_offset_gap_and_untraced_protocol_line_reject(self):
        self.events[0]["payload"]["stream_byte_offset"] += 1; self.rechain()
        with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
            self.check()
        self.events[0]["payload"]["stream_byte_offset"] -= 1; self.rechain()
        self.artifacts["W1/domain_A.stdout.log"] += self.events[2]["payload"]["raw_line_utf8"].encode()
        with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
            self.check()

    def test_rehashed_trace_cannot_read_valid_stdout_lines_backwards(self):
        self.check()
        first, second = self.events[2], self.events[4]
        raw = self.artifacts['W1/domain_A.stdout.log']
        one = first['payload']['raw_line_utf8'].encode(); two = second['payload']['raw_line_utf8'].encode()
        start, end = first['payload']['stream_byte_offset'], second['payload']['stream_byte_offset']
        self.assertEqual(end, start + len(one))
        self.artifacts['W1/domain_A.stdout.log'] = raw[:start] + two + one + raw[end + len(two):]
        first['payload']['stream_byte_offset'] = start + len(two)
        second['payload']['stream_byte_offset'] = start
        self.rechain()
        with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'):
            self.check()

    def test_trace_gap_previous_hash_and_repeated_receipt_reject(self):
        for field, value in [("sequence", 7), ("previous_event_sha256", "0" * 64)]:
            self.rechain(); original = copy.deepcopy(self.events[1]); self.events[1][field] = value
            self.artifacts["W1/harness.jsonl"] = b"".join(stored_json_bytes(event) for event in self.events)
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
                    self.check()
            self.events[1] = original
        self.rechain(); self.case["materialization_receipts"] = [{"invented": True}]
        with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
            self.check()


class ProtocolConnectionTests(unittest.TestCase):
    """Synthetic messages prove connection guards; no fixture is live evidence."""

    def setUp(self):
        self.policy = json.loads(CONTRACT_PATH.read_bytes())
        self.definitions = self.policy['wire_schemas']
        self.directory = tempfile.TemporaryDirectory(prefix='city-protocol-connection-', dir='/private/tmp')
        self.addCleanup(self.directory.cleanup)
        self.trace = RawTraceWriter(CONTRACT_PATH.read_bytes(), Path(self.directory.name) / 'harness.jsonl')
        self.addCleanup(self.trace.close)
        self.startup = schema_example(self.definitions['startup'], self.definitions)
        self.startup.update(witness_id='W1', domain='domain_A', launch_id='offline_A', pid=42)
        self.binding = schema_example(self.definitions['process_binding'], self.definitions)
        self.binding.update(witness_id='W1', domain='domain_A', launch_id='offline_A', pid=42,
                            startup_sha256=hashlib.sha256(stored_json_bytes(self.startup)).hexdigest())
        self.messages = [self.startup]
        self.sent = []
        self.offset = 0
        self.mutation = None
        test = self
        class FixtureMonitor:
            def next_protocol_line(self, timeout):
                if not test.messages:
                    raise EOFError('lcer.original_stdout_eof')
                raw = stored_json_bytes(test.messages.pop(0))
                offset = test.offset; test.offset += len(raw)
                return offset, raw

            def send(self, raw, timeout):
                request = parse_stored_json(raw)
                offset = sum(len(previous) for previous in test.sent)
                test.sent.append(raw)
                kind = test.policy['schema_contract']['response_match'][request['command']]
                payload = schema_example(test.definitions[kind], test.definitions)
                for key in ('witness_id', 'domain', 'launch_id', 'operation_id', 'binding_sha256'):
                    if key in payload:
                        payload[key] = request[key]
                if request['command'] == 'bind':
                    payload['startup_sha256'] = test.binding['startup_sha256']
                if request['command'] == 'emit':
                    physical = payload['physical_event']
                    for key in ('witness_id', 'domain', 'launch_id', 'operation_id', 'binding_sha256'):
                        physical[key] = request[key]
                    test.messages.append(copy.deepcopy(physical))
                response = {**request, 'schema': 'city.live_evidence_response.v1', 'status': 'ok', 'error': None, 'payload': payload}
                if test.mutation is not None:
                    test.mutation(response)
                test.messages.append(response)
                return offset
        self.connection = OriginalProtocolConnection(CONTRACT_PATH.read_bytes(), 'W1', 'domain_A', 'offline_A', FixtureMonitor(), self.trace)

    def _bind(self):
        self.assertEqual(self.connection.read_startup(), self.startup)
        result = self.connection.bind(self.binding)
        self.assertEqual(result['response']['status'], 'ok')

    def test_startup_binding_and_exact_response_are_traced(self):
        self._bind()
        result = self.connection.request('inspect', 'inspect_L0')
        self.assertEqual(result['response']['command'], 'inspect')
        self.assertEqual(len(self.trace.rows()), 5)
        self.assertEqual(self.trace.rows()[0]['payload']['parsed_schema'], 'startup')
        self.assertEqual(self.connection.binding_sha256, hashlib.sha256(stored_json_bytes(self.binding)).hexdigest())

    def test_unbound_duplicate_unknown_and_post_shutdown_commands_never_write(self):
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            self.connection.request('emit', 'emit_0001')
        self.assertEqual(self.sent, [])
        self._bind()
        self.connection.request('inspect', 'inspect_L0')
        count = len(self.sent)
        for command, operation in [('inspect', 'inspect_L0'), ('inspect', 'inspect_other'), ('bind', 'bind_0001')]:
            with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
                self.connection.request(command, operation)
        self.assertEqual(len(self.sent), count)
        self.connection.request('shutdown', 'shutdown_0001')
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            self.connection.request('inspect', 'inspect_terminal')
        self.assertEqual(len(self.sent), count + 1)

    def test_binding_rejects_changed_startup_identity_before_dispatch(self):
        self.connection.read_startup()
        with self.assertRaisesRegex(ValueError, '^lcer.process_identity_mismatch$'):
            self.connection.bind({**self.binding, 'startup_sha256': 'f' * 64})
        self.assertEqual(self.sent, [])

    def test_direct_exchange_cannot_skip_startup_or_replace_binding(self):
        self.connection.read_startup()
        changed = {**self.binding, 'startup_sha256': 'f' * 64}
        with self.assertRaisesRegex(ValueError, '^lcer.process_identity_mismatch$'):
            self.connection._exchange('bind', 'bind_0001', changed, hashlib.sha256(stored_json_bytes(changed)).hexdigest(), 5)
        self.assertEqual(self.sent, [])
        self.connection.bind(self.binding)
        count = len(self.sent)
        with self.assertRaisesRegex(ValueError, '^lcer.binding_mismatch$'):
            self.connection._exchange('inspect', 'inspect_L0', None, 'f' * 64, 5)
        self.assertEqual(len(self.sent), count)

    def test_f18_changes_only_outer_binding_after_the_required_prefix(self):
        self.startup['witness_id'] = 'F18'
        self.binding.update(witness_id='F18', startup_sha256=hashlib.sha256(stored_json_bytes(self.startup)).hexdigest())
        self.connection = OriginalProtocolConnection(CONTRACT_PATH.read_bytes(), 'F18', 'domain_A', 'offline_A',
                                                     self.connection.monitor, self.trace)
        self._bind()
        r1 = (CONTRACT_PATH.parent / 'ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R1.json').read_bytes()
        projection = {'schema': 'city.live_evidence_projection.v1', 'witness_id': 'F18', 'domain': 'domain_A',
                      'launch_id': 'offline_A', 'operation_id': 'materialize_0002', 'binding_sha256': self.connection.binding_sha256,
                      'record_role': 'R1', 'record_raw_sha256': hashlib.sha256(r1).hexdigest(),
                      'record_canonical_hash': hashlib.sha256(r1[:-1]).hexdigest(), 'generation': 1, 'allocation_owner': 'domain_A'}
        payload = {'projection': projection, 'record_raw_utf8': r1.decode(), 'launch_receipt_raw_utf8': None}
        count = len(self.sent)
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            self.connection.request('materialize', 'materialize_0002', payload)
        self.assertEqual(len(self.sent), count)
        self.connection.request('materialize', 'materialize_0001', schema_example(self.definitions['materialize_input'], self.definitions))
        self.connection.request('inspect', 'inspect_L0')
        self.connection.request('emit', 'emit_0001')
        for operation in ('inspect_L1', 'inspect_L2', 'inspect_L3'):
            self.connection.request('inspect', operation)
        def rejection(response):
            response.update(status='error', error={'code': 'lcer.binding_mismatch',
                            'underlying_code': 'lcer.binding_mismatch', 'stage': 'materialize_0002'}, payload=None)
        self.mutation = rejection
        result = self.connection.request('materialize', 'materialize_0002', payload)
        fault = result['fault_events'][0]
        before = parse_stored_json(base64.b64decode(fault['before']['raw_base64']))
        after_raw = base64.b64decode(fault['after']['raw_base64'])
        after = parse_stored_json(after_raw)
        self.assertEqual(after, {**before, 'binding_sha256': '0' * 64})
        self.assertEqual(after_raw, self.sent[-1])
        self.assertEqual(before['payload'], payload)
        self.assertEqual(fault['underlying_code'], 'lcer.binding_mismatch')
        self.assertEqual(self.trace.rows()[-1]['payload'], fault)
        self.mutation = None
        self.connection.request('inspect', 'inspect_terminal')
        self.assertEqual(parse_stored_json(self.sent[-1])['binding_sha256'], self.connection.binding_sha256)

    def test_wrong_response_binding_permanently_closes_connection(self):
        self._bind()
        self.mutation = lambda response: response.update(binding_sha256='f' * 64)
        with self.assertRaisesRegex(ValueError, '^lcer.protocol_response_mismatch$'):
            self.connection.request('inspect', 'inspect_L0')
        count = len(self.sent)
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            self.connection.request('inspect', 'inspect_terminal')
        self.assertEqual(len(self.sent), count)

    def test_emit_requires_the_separate_matching_physical_event(self):
        self._bind()
        result = self.connection.request('emit', 'emit_0001')
        self.assertEqual(result['physical_event'], result['response']['payload']['physical_event'])
        self.assertEqual([row['payload']['parsed_schema'] for row in self.trace.rows()][-2:], ['physical_event', 'response'])

    def test_rehashed_response_cannot_replace_the_observed_physical_event(self):
        self._bind()
        def mutate(response):
            response['payload']['physical_event']['actor_id'] += '_changed'
        self.mutation = mutate
        with self.assertRaisesRegex(ValueError, '^lcer.protocol_event_mismatch$'):
            self.connection.request('emit', 'emit_0001')


class WorldOracleTests(unittest.TestCase):
    """Raw-row fixtures test independent predicates only. No Unreal census claim."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier; self.policy = json.loads(CONTRACT_PATH.read_bytes())
        self.class_parents = {"/Script/CoreUObject.Object": None, "/Script/Engine.Actor": "/Script/CoreUObject.Object",
            "/Script/Engine.Pawn": "/Script/Engine.Actor", "/Script/Engine.Character": "/Script/Engine.Pawn",
            "/Script/Engine.Controller": "/Script/Engine.Actor", "/Script/Engine.PlayerController": "/Script/Engine.Controller",
            "/Script/CityLiveEvidenceProof.CityLiveEvidenceActor": "/Script/Engine.Actor",
            "/Script/CityLiveEvidenceProof.CityLiveEvidenceHeadAnchor": "/Script/CityLiveEvidenceProof.CityLiveEvidenceActor",
            "/Script/CityLiveEvidenceProof.CityLiveEvidenceResource": "/Script/CityLiveEvidenceProof.CityLiveEvidenceActor",
            "/Script/CityMaterializationProof.CityOldActor": "/Script/Engine.Actor"}
        self.raw0 = (CONTRACT_PATH.parent / "ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R0.json").read_bytes()
        self.raw1 = (CONTRACT_PATH.parent / "ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R1.json").read_bytes()
        self.world = {"world_path": "/Engine/Maps/Entry.Entry", "world_type": "Game", "game_mode_class": self.policy["runtime"]["game_mode"],
                      "actor_array_size": 0, "visited_slots": [], "null_slots": [], "actors": []}

    def actor(self, name, role=None, generation=None, owner=None, class_path=None):
        path = self.world["world_path"] + ":PersistentLevel." + name
        return {"actor_id": self.world["world_path"] + "|" + path, "actor_path": path, "world_path": self.world["world_path"],
                "class_path": class_path or ("/Script/CityLiveEvidenceProof.CityLiveEvidenceHeadAnchor" if role == "head_anchor"
                                             else "/Script/CityLiveEvidenceProof.CityLiveEvidenceResource"),
                "role": role, "domain": None if role is None else "domain_A", "generation": generation,
                "record_raw_sha256": None if generation is None else hashlib.sha256(self.raw0 if generation == 0 else self.raw1).hexdigest(),
                "allocation_owner": owner, "pending_kill": False, "auto_receive_input": 0}

    def census(self, actors):
        self.world["actors"] = sorted(actors, key=lambda row: row["actor_path"])
        self.world["actor_array_size"] = len(actors) + 1
        self.world["visited_slots"] = list(range(len(actors) + 1)); self.world["null_slots"] = [len(actors)]
        return self.verifier._world_facts(self.policy, [self.world], self.class_parents)

    def errors(self, facts, generation=1):
        return self.verifier._representation_errors(facts, facts["summary"], self.raw0 if generation == 0 else self.raw1,
                                                     generation, None if generation == 0 else "domain_A", "domain_A")

    def test_current_and_stale_r0_and_current_r1_are_distinct_valid_pairs(self):
        for generation in (0, 1):
            facts = self.census([self.actor("Anchor", "head_anchor", generation),
                                 self.actor("Resource", "resource_state", generation, None if generation == 0 else "domain_A")])
            self.assertEqual(self.errors(facts, generation), [])
            if generation == 0:
                self.assertIn("generation", self.errors(facts, 1))

    def test_generation_precedes_cardinality_and_invalid_rows_are_retained(self):
        facts = self.census([self.actor("Anchor", "head_anchor", 1), self.actor("Resource", "resource_state", 1, "domain_A"),
                             self.actor("OldResource", "resource_state", 0)])
        self.assertEqual(self.errors(facts)[:2], ["generation", "cardinality"])
        self.assertIsNone(facts["summary"]["record_sha256"]); self.assertIsNone(facts["summary"]["generation"])
        self.assertEqual(len(facts["relevant"]), 3)
        partial = self.census([self.actor("Resource", "resource_state", 1, "domain_A")])
        self.assertEqual(self.errors(partial), ["cardinality"])
        self.assertEqual(partial["summary"]["anchor_count"], 0)

    def test_wrong_owner_extra_resource_and_pending_actor_reject(self):
        anchor = self.actor("Anchor", "head_anchor", 1); resource = self.actor("Resource", "resource_state", 1, "domain_B")
        self.assertEqual(self.errors(self.census([anchor, resource])), ["owner"])
        resource["allocation_owner"] = "domain_A"
        self.assertEqual(self.errors(self.census([anchor, resource, self.actor("Extra", "resource_state", 1, "domain_A")])), ["cardinality"])
        resource["pending_kill"] = True
        self.assertEqual(self.errors(self.census([anchor, resource])), ["cardinality"])

    def test_slot_omission_duplicate_and_incomplete_range_reject(self):
        self.census([self.actor("Anchor", "head_anchor", 1), self.actor("Resource", "resource_state", 1, "domain_A")])
        original = copy.deepcopy(self.world)
        for defect in ("omitted_actor_row", "duplicate_slot", "missing_slot"):
            self.world = copy.deepcopy(original)
            if defect == "omitted_actor_row": self.world["actors"].pop()
            if defect == "duplicate_slot": self.world["visited_slots"].append(0)
            if defect == "missing_slot": self.world["visited_slots"].pop()
            with self.subTest(defect=defect):
                with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
                    self.verifier._world_facts(self.policy, [self.world], self.class_parents)

    def test_wrong_game_mode_world_and_forged_summary_reject(self):
        facts = self.census([self.actor("Anchor", "head_anchor", 1), self.actor("Resource", "resource_state", 1, "domain_A")])
        changed = dict(facts["summary"], anchor_count=2)
        self.assertEqual(self.verifier._representation_errors(facts, changed, self.raw1, 1, "domain_A", "domain_A"), ["summary"])
        self.world["game_mode_class"] = "/Script/Engine.GameModeBase"
        facts = self.verifier._world_facts(self.policy, [self.world], self.class_parents)
        self.assertEqual(self.errors(facts)[0], "wrong_world")
        self.world["world_type"] = "EditorPreview"
        facts = self.verifier._world_facts(self.policy, [self.world], self.class_parents)
        self.assertEqual(self.errors(facts)[0], "wrong_world")

    def test_startup_counts_unpossessed_pawn_independently_of_controller(self):
        controller = self.actor("Controller", class_path="/Script/Engine.PlayerController")
        self.census([controller])
        startup = schema_example(self.policy["wire_schemas"]["startup"], self.policy["wire_schemas"])
        startup["worlds"] = [self.world]
        startup["controllers"] = [{"actor_path": controller["actor_path"], "class_path": controller["class_path"], "pawn_path": None}]
        self.verifier._startup_world(self.policy, startup, self.class_parents)
        self.census([controller, self.actor("Unpossessed", class_path="/Script/Engine.Character")])
        with self.assertRaisesRegex(ValueError, "^lcer.release_evidence_invalid$"):
            self.verifier._startup_world(self.policy, startup, self.class_parents)


class CasePrefixExecutionTests(unittest.TestCase):
    """Record transport fixtures exercise real canonical calls and parent checks.

    Nothing in this class launches Unreal or supplies live acceptance evidence.
    """

    def setUp(self):
        self.raw = CONTRACT_PATH.read_bytes()
        self.policy = json.loads(self.raw)
        self.temporary = tempfile.TemporaryDirectory(prefix='city-case-prefix-', dir='/private/tmp')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        import concurrent_external_evidence_arbitration as canonical
        self.canonical = canonical
        world_fixture = WorldOracleTests()
        world_fixture.setUp()
        self.parents = world_fixture.class_parents
        self.counter = 0

    def execution(self, case, artifact_wire=False):
        from types import SimpleNamespace
        self.counter += 1
        log = []
        cohort = object.__new__(AcquisitionProcessCohort)
        cohort._contract_raw = self.raw
        cohort.case_id = case
        output = self.root / ('artifacts-%s-%d' % (case, self.counter))
        if artifact_wire:
            (output / case).mkdir(parents=True, mode=0o700)
        cohort.workspace = SimpleNamespace(_repository_root=CONTRACT_PATH.parent.parent, _output_root=output, verify=lambda: None)
        trace_path = output / case / 'harness.jsonl' if artifact_wire else self.root / ('%s-%d.jsonl' % (case, self.counter))
        cohort.trace = RawTraceWriter(self.raw, trace_path)
        self.addCleanup(cohort.trace.close)
        connections = {}
        fixture = ProcessBindingRelationTests()
        fixture.setUp()
        faults = {}

        class Connection:
            def __init__(connection, domain, index):
                connection.domain = domain
                connection.startup = copy.deepcopy(fixture.startup)
                connection.startup.update(witness_id=case, domain=domain, launch_id='offline_' + case + domain, pid=12000 + index)
                connection.startup_raw = stored_json_bytes(connection.startup)
                connection.root = str(self.root / case / domain)
                values = dict(engine=self.policy['runtime']['engine'], absolute_city_project=fixture.project['realpath'],
                              absolute_domain_root=connection.root, observed_operator_user=fixture.operator,
                              witness_id=case, domain=domain, launch_id=connection.startup['launch_id'])
                connection.launch = {'process_root_realpath': connection.root,
                                     'environment': {key: value.format_map(values) for key, value in self.policy['launch_environment'].items()}}
                connection.process = copy.deepcopy(fixture.observation)
                connection.process.update(pid=connection.startup['pid'], startup=copy.deepcopy(connection.startup),
                                          argv=[value.format_map(values) for value in self.policy['launch_argv']],
                                          environment=connection.launch['environment'])
                for row in connection.process['descriptors']:
                    row['pid'] = connection.startup['pid']
                    row['kernel_id'] += domain
                    row['peer_kernel_id'] += domain
                connection.binding = None
                connection.record = None
                connection.generation = None
                connection.receipt = None

            def bind(connection, binding, timeout=60):
                log.append(('bind', connection.domain))
                connection.binding = copy.deepcopy(binding)
                return {'response': {'status': 'ok'}}

            def actor(connection, role):
                world = '/Engine/Maps/Entry.Entry'
                path = world + ':PersistentLevel.' + connection.domain + '_' + role
                return {'actor_id': world + '|' + path, 'actor_path': path, 'world_path': world,
                        'class_path': '/Script/CityLiveEvidenceProof.' + ('CityLiveEvidenceHeadAnchor' if role == 'head_anchor' else 'CityLiveEvidenceResource'),
                        'role': role, 'domain': connection.domain, 'generation': connection.generation,
                        'record_raw_sha256': hashlib.sha256(connection.record).hexdigest(),
                        'allocation_owner': None if role == 'head_anchor' else parse_stored_json(connection.record)['current_causal_state']['shared_slot']['allocation_owner'],
                        'pending_kill': False, 'auto_receive_input': 0}

            def request(connection, command, operation, payload=None, timeout=60):
                log.append((command, connection.domain, operation, 'begin'))
                if faults.get('transport') == (command, connection.domain, operation):
                    raise TimeoutError('lcer.operation_timeout')
                routing = {key: connection.binding[key] for key in ('witness_id', 'domain', 'launch_id')}
                routing.update(operation_id=operation, binding_sha256=hashlib.sha256(stored_json_bytes(connection.binding)).hexdigest())
                if command == 'materialize':
                    connection.record = payload['record_raw_utf8'].encode()
                    connection.generation = payload['projection']['generation']
                    if connection.generation == 0:
                        receipt = self.canonical.materialization_acceptance_receipt(parse_stored_json(connection.record), connection.domain, routing['launch_id'])
                        result = {'r0_acceptance_raw_utf8': stored_json_bytes(receipt).decode(), 'r1_representation': None}
                    else:
                        receipt = {key: payload['projection'][key] for key in ('record_raw_sha256', 'record_canonical_hash', 'generation', 'allocation_owner')}
                        receipt.update(schema='city.live_evidence_representation_receipt.v1', **routing,
                                       anchor_actor_id=connection.actor('head_anchor')['actor_id'],
                                       resource_actor_id=connection.actor('resource_state')['actor_id'], proposal_capability_enabled=False)
                        result = {'r0_acceptance_raw_utf8': None, 'r1_representation': receipt}
                    connection.receipt = copy.deepcopy(result)
                    if faults.get('receipt') == (connection.domain, operation):
                        result = copy.deepcopy(result)
                        result['r1_representation']['anchor_actor_id'] = 'forged_actor'
                elif command == 'inspect':
                    world = copy.deepcopy(connection.startup['worlds'][0])
                    actors = [*world['actors'], connection.actor('head_anchor'), connection.actor('resource_state')]
                    if faults.get('owner') == (connection.domain, operation):
                        actors[-1]['allocation_owner'] = 'domain_B'
                    world.update(actors=sorted(actors, key=lambda row: row['actor_path']), actor_array_size=len(actors),
                                 visited_slots=list(range(len(actors))), null_slots=[])
                    result = {'schema': 'city.live_evidence_observation.v1', **routing, 'worlds': [world],
                              'selected_world_path': world['world_path'], 'anchor_count': 1, 'resource_actor_count': 1,
                              'all_proof_actor_ids': sorted(row['actor_id'] for row in actors if row['role'] is not None),
                              'record_sha256': hashlib.sha256(connection.record).hexdigest(), 'generation': connection.generation,
                              'allocation_owner': connection.actor('resource_state')['allocation_owner']}
                elif command == 'emit':
                    record = parse_stored_json(connection.record)
                    q = self.canonical.external_evidence_q(record, connection.domain)
                    q_raw = stored_json_bytes(q)
                    fields = {'physical_event_id': q['physical_event_id'], 'interaction_counter': 1,
                              'q_raw_sha256': hashlib.sha256(q_raw).hexdigest(), 'q_canonical_hash': self.canonical.q_hash(q)}
                    event = {'schema': 'city.live_evidence_physical_event.v1', **routing, **fields,
                             'actor_id': connection.actor('resource_state')['actor_id'],
                             'accepted_record_raw_sha256': hashlib.sha256(connection.record).hexdigest()}
                    result = {'q_raw_utf8': q_raw.decode(), 'physical_event': event,
                              'wrapper': {'schema': 'city.live_evidence_emission.v1', **routing, **fields,
                                          'source_record_hash': self.canonical.canonical_hash(record)},
                              'acceptance_receipt_raw_utf8': connection.receipt['r0_acceptance_raw_utf8'],
                              'emission_receipt_raw_utf8': stored_json_bytes(self.canonical.evidence_emission_receipt(record, q, connection.domain, routing['launch_id'])).decode()}
                    if faults.get('actor') == connection.domain:
                        result['physical_event']['actor_id'] = 'other_actor'
                else:
                    raise AssertionError(command)
                log.append((command, connection.domain, operation, 'end'))
                return {'response': {'status': 'ok', 'payload': result}}

        for index, domain in enumerate(('domain_A', 'domain_B')):
            connections[domain] = Connection(domain, index)

        def start():
            log.extend([('launch', 'domain_A'), ('launch', 'domain_B')])

        def ready(timeout=60):
            log.extend([('ready', 'domain_A'), ('ready', 'domain_B')])
            return {key: copy.deepcopy(value.startup) for key, value in connections.items()}

        def sample(domain, checkpoint):
            log.append(('sample', domain, checkpoint, execution.canonical.publication_count))
            connection = connections[domain]
            exited = faults.get('exit') == (domain, checkpoint)
            return {'checkpoint': checkpoint, 'domain': domain, 'launch_id': connection.startup['launch_id'],
                    'poll_returncode': faults.get('exit_code', 0) if exited else None,
                    'observed_process': None if exited else copy.deepcopy(connection.process), 'pipe_endpoints': [], 'pipe_holders': []}

        cohort.start_originals = start
        cohort.read_startups = ready
        cohort.sample = sample
        cohort.connection = lambda domain: connections[domain]
        cohort.launch_record = lambda domain: copy.deepcopy(connections[domain].launch)
        cohort.is_alive = lambda domain: faults.get('exit') != (domain, 'terminal')
        if artifact_wire:
            # Use the actual original protocol implementation over a deterministic
            # record transport. These stored bytes are test fixtures, not Unreal.
            cohort._entries = {}
            cohort._closed = False
            cohort._budget = CaptureBudget(64 * 1024 * 1024)
            wrappers = {}

            class Monitor:
                def __init__(monitor, backend):
                    monitor.backend = backend
                    monitor.pending = []
                    monitor.input = bytearray()
                    monitor.closed = False
                    monitor.stdout = output / case / (backend.domain + '.stdout.log')
                    monitor.stderr = output / case / (backend.domain + '.stderr.log')
                    monitor.stdout.write_bytes(b'')
                    monitor.stderr.write_bytes(b'offline record transport fixture\n')
                    monitor.write(backend.startup)

                def write(monitor, value):
                    raw = stored_json_bytes(value)
                    offset = monitor.stdout.stat().st_size
                    with monitor.stdout.open('ab') as stream:
                        stream.write(raw)
                    monitor.pending.append((offset, raw))

                def next_protocol_line(monitor, timeout):
                    if not monitor.pending:
                        raise EOFError('fixture_protocol_empty')
                    return monitor.pending.pop(0)

                def send(monitor, raw, timeout=60):
                    offset = len(monitor.input)
                    monitor.input.extend(raw)
                    command = parse_stored_json(raw)
                    routing = {key: command[key] for key in ('witness_id', 'domain', 'launch_id', 'operation_id', 'binding_sha256')}
                    if command['command'] == 'bind':
                        monitor.backend.bind(command['payload'], timeout)
                        payload = {'schema': 'city.live_evidence_bind_ack.v1', **routing,
                                   'startup_sha256': command['payload']['startup_sha256']}
                    elif command['command'] == 'shutdown':
                        log.append(('shutdown', monitor.backend.domain))
                        payload = {'schema': 'city.live_evidence_shutdown_ack.v1', **routing, 'accepted': True}
                    else:
                        response = monitor.backend.request(command['command'], command['operation_id'], command['payload'], timeout)['response']
                        payload = response['payload']
                        if command['command'] == 'emit':
                            monitor.write(payload['physical_event'])
                    monitor.write({'schema': 'city.live_evidence_response.v1', **routing, 'command': command['command'],
                                   'status': 'ok', 'payload': payload, 'error': None})
                    return offset

                def stdin_bytes(monitor):
                    return bytes(monitor.input)

                def observation(monitor):
                    return {'stream_sizes': {'stdout': monitor.stdout.stat().st_size, 'stderr': monitor.stderr.stat().st_size},
                            'eof': ['stderr', 'stdout'] if monitor.closed else [], 'finished': monitor.closed,
                            'failure': None, 'poll_returncode': 0 if monitor.closed else None}

            for domain, backend in connections.items():
                monitor = Monitor(backend)
                wrappers[domain] = OriginalProtocolConnection(self.raw, case, domain, backend.startup['launch_id'], monitor, cohort.trace)
                launch = dict(backend.launch, witness_id=case, domain=domain, launch_id=backend.startup['launch_id'])
                cohort._entries[domain] = {'launch': launch, 'monitor': monitor}

            def wire_ready(timeout=60):
                values = {}
                for domain in ('domain_A', 'domain_B'):
                    log.append(('ready', domain))
                    values[domain] = wrappers[domain].read_startup(timeout)
                return values

            def wire_sample(domain, checkpoint):
                value = sample(domain, checkpoint)
                if value['observed_process'] is not None:
                    cohort.trace.append('process_observation', value['observed_process'], domain)
                cohort.trace.append('liveness', value, domain)
                return value

            def cleanup(timeout=60):
                result = {'processes': [], 'liveness': [], 'errors': []}
                for domain, connection in wrappers.items():
                    connection.request('shutdown', 'shutdown_0001', timeout=timeout)
                    monitor = connection.monitor
                    if faults.get('untraced_output') == domain:
                        monitor.write({'extra': 'unconsumed output'})
                    monitor.closed = True
                    faults.update(exit=(domain, 'cleanup'), exit_code=0)
                    result['liveness'].append(wire_sample(domain, 'cleanup'))
                    result['processes'].append({'process': domain, 'pid': connections[domain].process['pid'], 'poll_returncode': 0,
                                                'shutdown_requested': True, 'kill_sent': False, 'streams': monitor.observation()})
                cohort._closed = True
                if faults.get('cleanup_error'):
                    result['errors'].append({'process': 'domain_A', 'stage': 'fixture', 'code': 'fixture_cleanup_error'})
                if faults.get('artifact_extra'):
                    (output / case / 'undeclared.bin').write_bytes(b'extra')
                return result

            cohort.connection = lambda domain: wrappers[domain]
            cohort.read_startups = wire_ready
            cohort.sample = wire_sample
            cohort.cleanup = cleanup
        execution = CasePrefixExecution(cohort, LiveWorldAcceptance(self.raw, self.parents))
        return execution, log, faults

    def test_all_eight_witness_orders_execute_actual_canonical_publication(self):
        for witness in self.policy['witnesses']:
            with self.subTest(case=witness['id']):
                execution, log, _ = self.execution(witness['id'])
                result = execution.run_prefix('P5')
                self.assertFalse(result['live_acceptance_verified'])
                self.assertEqual(result['publication_count'], 1)
                self.assertTrue(execution.canonical._core.canonical_coverage()['canonical_prefix_complete'])
                self.assertEqual(log[:4], [('launch', 'domain_A'), ('launch', 'domain_B'), ('ready', 'domain_A'), ('ready', 'domain_B')])
                emitted = [(row[1], row[-1]) for row in log if row[0] == 'emit']
                self.assertEqual(emitted, [(domain, edge) for domain in witness['emission'] for edge in ('begin', 'end')])
                refreshed = [row[1] for row in log if row[0] == 'materialize' and row[2:] == ('materialize_0002', 'begin')]
                self.assertEqual(refreshed, witness['refresh'])
                calls = execution.canonical._core.retained_calls()
                self.assertEqual([parse_stored_json(row['arguments']['q_object_raw_utf8'].encode())['source']['domain'] for row in calls[:2]], witness['presentation'])
                for checkpoint, published in (('before_resolve', 0), ('after_resolve', 1)):
                    self.assertEqual([row[3] for row in log if row[0] == 'sample' and row[2] == checkpoint], [published, published])
                events = [row['payload'] for row in execution.trace.rows() if row['event_id'] == 'head_event']
                self.assertEqual(len([row for row in events if row['edge'] == 'publish']), 1)
                self.assertEqual(execution._dispositions, {'domain_A': 'current', 'domain_B': 'current'})
                at_l4 = [row for row in events if row['edge'] == 'classify' and row['observation_sha256'] is not None][-4:-2]
                self.assertEqual({row['domain']: row['disposition'] for row in at_l4},
                                 {domain: 'current' if domain == witness['refresh'][0] else 'stale' for domain in ('domain_A', 'domain_B')})

    def test_every_failure_and_canonical_fault_stops_at_its_exact_prefix(self):
        cases = FrozenObligationPlanCompiler(self.raw).compile()['frozen_case_plans']
        for name, case in cases.items():
            if case['kind'] == 'witness':
                continue
            with self.subTest(case=name):
                execution, log, _ = self.execution(name)
                execution.run_prefix(case['prefix'])
                self.assertEqual(execution._prefix, int(case['prefix'][1]))
                self.assertFalse(any(row[0] == 'materialize' and row[2] == 'materialize_0002' for row in log if len(row) > 2))
                with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
                    execution.run_prefix('P' + str(int(case['prefix'][1]) + 1))

    def test_all_canonical_failure_actions_retain_actual_arguments_and_codes(self):
        cases = FrozenObligationPlanCompiler(self.raw).compile()['frozen_case_plans']
        for name, case in cases.items():
            if case['kind'] == 'witness':
                continue
            expected = case.get('underlying_code') or case['failure_program']['underlying_code']
            if not expected.startswith('concurrent_external_'):
                continue
            with self.subTest(case=name):
                execution, log, _ = self.execution(name)
                execution.run_prefix(case['prefix'])
                result = execution.run_failure()
                self.assertEqual(result['underlying_code'], expected)
                self.assertFalse(result['live_acceptance_verified'])
                self.assertTrue(execution.canonical._core.canonical_coverage()['canonical_prefix_complete'])
                self.assertEqual(execution.canonical.publication_count, case['publication_count'])
                calls = execution.canonical._core.retained_calls()
                self.assertEqual(calls[-1]['exception_code'], expected)
                self.assertIsNone(calls[-1]['return_raw_utf8'])
                self.assertIsNone(calls[-1]['published_record_raw_utf8'])
                events = [row['payload'] for row in execution.trace.rows() if row['event_id'] == 'fault_event']
                if case['kind'] == 'canonical_fault':
                    self.assertEqual(events, [])
                    self.assertEqual([row[3] for row in log if row[0] == 'sample' and row[2] in ('before_resolve', 'after_resolve')], [0] * 4)
                else:
                    self.assertEqual(len(events), 1)
                    event = events[0]
                    self.assertEqual(event['underlying_code'], expected)
                    self.assertEqual(base64.b64decode(event['after']['raw_base64']), stored_json_bytes(calls[-1]['arguments']))
                    if name in ('F01', 'F10a'):
                        self.assertEqual(event['before'], event['after'])
                    else:
                        self.assertNotEqual(event['before'], event['after'])
                    if name == 'F01':
                        self.assertFalse(any(row[0] == 'emit' and row[1] == 'domain_B' for row in log))
                        self.assertIsNone(execution.canonical.captures()[1]['emission'])
                before = list(log)
                with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
                    execution.run_failure()
                self.assertEqual(log, before)

    def test_terminal_census_follows_actual_rejection_without_another_canonical_call(self):
        for name in ('F01', 'F03', 'F10a', 'C01'):
            with self.subTest(case=name):
                execution, log, _ = self.execution(name)
                execution.run_prefix(execution.case['prefix'])
                execution.run_failure()
                calls = execution.canonical._core.retained_calls()
                result = execution.capture_terminal()
                self.assertFalse(result['live_acceptance_verified'])
                self.assertEqual(execution.canonical._core.retained_calls(), calls)
                for domain in ('domain_A', 'domain_B'):
                    self.assertEqual(log.count(('inspect', domain, 'inspect_terminal', 'begin')), 1)
                self.assertLess(log.index(('inspect', 'domain_B', 'inspect_terminal', 'end')),
                                next(i for i, row in enumerate(log) if row[0] == 'sample' and row[2] == 'terminal'))
                self.assertEqual(set(execution._dispositions.values()), {'stale' if name == 'F10a' else 'unclaimed'})
                with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
                    execution.capture_terminal()

    def test_terminal_failure_still_samples_both_originals_and_cannot_retry(self):
        execution, log, faults = self.execution('F03')
        execution.run_prefix('P1'); execution.run_failure()
        faults['transport'] = ('inspect', 'domain_A', 'inspect_terminal')
        with self.assertRaisesRegex(TimeoutError, '^lcer.operation_timeout$'):
            execution.capture_terminal()
        self.assertIn(('inspect', 'domain_B', 'inspect_terminal', 'end'), log)
        self.assertEqual([row[1] for row in log if row[0] == 'sample' and row[2] == 'terminal'], ['domain_A', 'domain_B'])
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            execution.capture_terminal()

    def test_failed_emission_prevents_peer_admission_and_all_retry(self):
        execution, log, faults = self.execution('W1')
        faults['transport'] = ('emit', 'domain_A', 'emit_0001')
        with self.assertRaisesRegex(TimeoutError, '^lcer.operation_timeout$'):
            execution.run_prefix('P5')
        self.assertFalse(any(row[0] == 'emit' and row[1] == 'domain_B' for row in log))
        self.assertEqual(execution.canonical._core.retained_calls(), [])
        before = list(log)
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
            execution.run_prefix('P1')
        self.assertEqual(log, before)

    def test_command_failures_send_only_the_declared_mutated_input(self):
        for name in ('F09', 'F17', 'F18'):
            with self.subTest(case=name):
                execution, log, _ = self.execution(name)
                execution.run_prefix(execution.case['prefix'])
                program = execution.case['failure_program']
                connection = execution.cohort.connection('domain_A')
                sent = []

                def request(command, operation, payload=None, timeout=60):
                    self.assertEqual((command, operation), ('materialize', 'materialize_0002'))
                    sent.append(copy.deepcopy(payload))
                    events = []
                    if name == 'F18':
                        before = execution._materialize_command_bytes('domain_A', payload)
                        after = parse_stored_json(before); after['binding_sha256'] = '0' * 64
                        events = [{**{key: program[key] for key in ('executor', 'stage', 'action')},
                                   'failure_case': name, 'consumed': True, 'underlying_code': program['underlying_code'],
                                   'before': execution._fault_bytes('materialize_command', before),
                                   'after': execution._fault_bytes('materialize_command', stored_json_bytes(after))}]
                        execution.trace.append('fault_event', events[0], 'domain_A', operation)
                    return {'response': {'status': 'error', 'error': {'underlying_code': program['underlying_code']}}, 'fault_events': events}

                connection.request = request
                result = execution.run_failure()
                self.assertEqual(result['underlying_code'], program['underlying_code'])
                self.assertEqual(len(sent), 1)
                if name == 'F09':
                    r0 = parse_stored_json(execution._initial_raw)
                    self.assertEqual(sent[0]['record_raw_utf8'], stored_json_bytes(self.canonical.working_state_projection(
                        r0, r0['current_causal_state'], r0['future_causal_state'])).decode())
                    self.assertEqual(sent[0]['projection']['record_role'], 'R1')
                    self.assertEqual(execution.canonical.publication_count, 0)
                elif name == 'F17':
                    self.assertEqual(sent[0]['record_raw_utf8'].encode(), execution._initial_raw)
                    self.assertEqual(sent[0]['projection']['record_role'], 'R0')
                    self.assertIsNotNone(sent[0]['launch_receipt_raw_utf8'])
                else:
                    self.assertEqual(sent[0]['record_raw_utf8'].encode(), execution.canonical.head_raw)
                event, = [row['payload'] for row in execution.trace.rows() if row['event_id'] == 'fault_event']
                before = parse_stored_json(base64.b64decode(event['before']['raw_base64']))
                after = parse_stored_json(base64.b64decode(event['after']['raw_base64']))
                self.assertEqual(after['payload'], sent[0])
                if name == 'F18':
                    before['binding_sha256'] = '0' * 64
                    self.assertEqual(before, after)
                else:
                    self.assertNotEqual(before['payload'], after['payload'])
                self.assertEqual(execution.canonical.publication_count, 0 if name == 'F09' else 1)

    def test_process_failure_actions_use_fresh_before_after_and_never_bind_replacement(self):
        for name in ('F07', 'F08', 'F11', 'F12'):
            with self.subTest(case=name):
                execution, log, faults = self.execution(name)
                execution.run_prefix(execution.case['prefix'])
                domain = execution.case['failure_program']['domain']
                original = execution.cohort.connection(domain)
                dead = []
                observations = []
                launch = copy.deepcopy(original.launch)
                startup = copy.deepcopy(original.startup)
                process = copy.deepcopy(original.process)
                startup.update(pid=startup['pid'] + 100, launch_id='replacement_fixture')
                launch['process_root_realpath'] += '_replacement'
                values = dict(engine=self.policy['runtime']['engine'], absolute_city_project=process['argv'][1],
                              absolute_domain_root=launch['process_root_realpath'], observed_operator_user=process['environment']['USER'],
                              witness_id=name, domain=domain, launch_id=startup['launch_id'])
                launch['environment'] = {key: value.format_map(values) for key, value in self.policy['launch_environment'].items()}
                process.update(pid=startup['pid'], startup=startup, argv=[value.format_map(values) for value in self.policy['launch_argv']], environment=launch['environment'])
                for row in process['descriptors']:
                    row.update(pid=startup['pid'], kernel_id=row['kernel_id'] + '_replacement', peer_kernel_id=row['peer_kernel_id'] + '_replacement')

                def snapshot(selected, checkpoint, replacement=False):
                    self.assertEqual(selected, domain)
                    observations.append((len(dead), replacement))
                    value = process if replacement else original.process
                    exited = bool(dead) and not replacement
                    return {'checkpoint': checkpoint, 'domain': domain, 'launch_id': value['startup']['launch_id'],
                            'poll_returncode': -15 if exited else None, 'observed_process': None if exited else copy.deepcopy(value),
                            'pipe_endpoints': [], 'pipe_holders': []}

                def terminate(selected, timeout=60):
                    self.assertEqual(selected, domain)
                    dead.append(True)
                    faults.update(exit=(domain, 'terminal'), exit_code=-15)
                    return -15

                def replacement(timeout=60):
                    self.assertEqual(dead, [True])
                    return {'launch': launch, 'startup': startup}

                execution.cohort.fault_snapshot = snapshot
                execution.cohort.terminate_original = terminate
                execution.cohort.start_replacement = replacement
                original_bind_count = sum(row[0] == 'bind' for row in log)
                result = execution.run_failure()
                self.assertEqual(result['underlying_code'], execution.case['failure_program']['underlying_code'])
                self.assertEqual(observations, [(0, False), (1, False)] + ([(1, True)] if name == 'F07' else []))
                self.assertEqual(sum(row[0] == 'bind' for row in log), original_bind_count)
                self.assertEqual(dead, [True])
                if name == 'F08':
                    self.assertFalse(any(row[0] == 'emit' and row[1] == 'domain_B' for row in log))
                event, = [row['payload'] for row in execution.trace.rows() if row['event_id'] == 'fault_event']
                self.assertIsNone(event['before']['sample']['poll_returncode'])
                if name != 'F07':
                    self.assertEqual(event['after']['sample']['poll_returncode'], -15)
                    self.assertIsNone(event['after']['sample']['observed_process'])
                else:
                    self.assertEqual(event['after']['sample']['observed_process']['pid'], startup['pid'])
                    self.assertNotEqual(event['after']['sample']['launch_id'], event['before']['sample']['launch_id'])
                terminal = execution.capture_terminal()
                self.assertNotIn(domain, terminal['observations'])
                self.assertEqual(terminal['liveness'][domain]['poll_returncode'], -15)
                self.assertIsNone(terminal['liveness'][domain]['observed_process'])
                self.assertEqual(execution._dispositions[domain], 'unavailable')

    def child_fault_execution(self, name, defect=None):
        execution, log, _ = self.execution(name)
        execution.run_prefix('P3')
        program = execution.case['failure_program']
        domain = program['domain']
        connection = execution.cohort.connection(domain)
        original = connection.request
        retained = {}

        def redraw(observation):
            world = observation['worlds'][0]
            actors = world['actors']
            world.update(actors=sorted(actors, key=lambda row: row['actor_path']), actor_array_size=len(actors),
                         visited_slots=list(range(len(actors))), null_slots=[])
            proof = [row for row in actors if row['role'] in ('head_anchor', 'resource_state')]
            anchors = [row for row in proof if row['role'] == 'head_anchor']
            resources = [row for row in proof if row['role'] == 'resource_state']
            def homogeneous(rows, key):
                values = {row[key] for row in rows}
                return values.pop() if len(values) == 1 else None
            observation.update(anchor_count=len(anchors), resource_actor_count=len(resources),
                               all_proof_actor_ids=sorted(row['actor_id'] for row in proof),
                               record_sha256=homogeneous(proof, 'record_raw_sha256'), generation=homogeneous(proof, 'generation'),
                               allocation_owner=homogeneous(resources, 'allocation_owner'))

        def request(command, operation, payload=None, timeout=60):
            if command == 'arm_fault':
                log.append(('arm_fault', domain, operation))
                self.assertEqual(payload, {'failure_case': name, 'stage': program['stage'], 'operation_id': 'materialize_0002'})
                binding = connection.binding
                ack = {key: binding[key] for key in ('witness_id', 'domain', 'launch_id')}
                ack.update(schema='city.live_evidence_fault_ack.v1', operation_id=operation,
                           binding_sha256=hashlib.sha256(stored_json_bytes(binding)).hexdigest(),
                           failure_case=name, stage=program['stage'], armed_for='materialize_0002')
                return {'response': {'status': 'ok', 'payload': ack}, 'fault_events': []}
            if command == 'inspect' and retained:
                log.append(('inspect', domain, operation, 'begin'))
                result = copy.deepcopy(retained['after'])
                result['operation_id'] = operation
                log.append(('inspect', domain, operation, 'end'))
                return {'response': {'status': 'ok', 'payload': result}, 'fault_events': []}
            result = original(command, operation, payload, timeout)
            self.assertEqual((command, operation), ('materialize', 'materialize_0002'))
            before = original('inspect', 'materialize_0002')['response']['payload']
            after = copy.deepcopy(before)
            world = after['worlds'][0]
            if name in ('F13', 'F14'):
                world['actors'] = [row for row in world['actors'] if row['role'] != 'head_anchor']
            elif name == 'F15':
                next(row for row in world['actors'] if row['role'] == 'resource_state')['allocation_owner'] = 'domain_B'
            else:
                extra = copy.deepcopy(next(row for row in world['actors'] if row['role'] == 'resource_state'))
                extra['actor_path'] += '_extra'
                extra['actor_id'] = extra['world_path'] + '|' + extra['actor_path']
                if name == 'F16b':
                    extra.update(generation=0, record_raw_sha256=hashlib.sha256(execution._initial_raw).hexdigest(), allocation_owner=None)
                world['actors'].append(extra)
            redraw(after)
            if name in ('F13', 'F14'):
                before = copy.deepcopy(after)
            event = {**{key: program[key] for key in ('executor', 'stage', 'action')}, 'failure_case': name,
                     'consumed': True, 'underlying_code': program['underlying_code'],
                     'before': {'kind': 'world', 'observation': before}, 'after': {'kind': 'world', 'observation': after}}
            retained['after'] = copy.deepcopy(after)
            if defect == 'changed_stage':
                event['stage'] = 'other_stage'
            if defect == 'unconsumed':
                event['consumed'] = False
            if defect == 'changed_hook_world':
                next(row for row in event['after']['observation']['worlds'][0]['actors'] if row['role'] == 'resource_state')['auto_receive_input'] = 1
            events = [] if defect == 'missing_event' else [event]
            for value in events:
                execution.trace.append('wire_event', {'direction': 'stdout', 'parsed_schema': 'fault_event',
                    'raw_line_utf8': stored_json_bytes(value).decode(), 'stream_byte_offset': 0}, domain, operation)
            if name in ('F13', 'F14'):
                return {'response': {'status': 'error', 'error': {'underlying_code': program['underlying_code']}}, 'fault_events': events}
            return {**result, 'fault_events': events}

        connection.request = request
        return execution, log

    def test_all_five_child_actions_require_the_actual_expected_world_failure(self):
        for name in ('F13', 'F14', 'F15', 'F16a', 'F16b'):
            with self.subTest(case=name):
                execution, log = self.child_fault_execution(name)
                result = execution.run_failure()
                self.assertEqual(result['underlying_code'], execution.case['failure_program']['underlying_code'])
                self.assertEqual(result['publication_count'], 1)
                self.assertFalse(result['live_acceptance_verified'])
                self.assertEqual(len(execution._wire_faults), 1)
                domain = execution.case['failure_program']['domain']
                self.assertLess(log.index(('arm_fault', domain, 'arm_fault_0001')),
                                log.index(('materialize', domain, 'materialize_0002', 'begin')))
                if name not in ('F13', 'F14'):
                    for peer in ('domain_A', 'domain_B'):
                        self.assertIn(('inspect', peer, 'inspect_L4', 'end'), log)
                self.assertEqual(execution.canonical.head_raw, execution.canonical._core._r1)
                terminal = execution.capture_terminal()
                self.assertEqual(terminal['underlying_code'], result['underlying_code'])
                self.assertEqual(execution._dispositions[domain], 'unavailable' if name in ('F13', 'F14') else 'unclaimed')
                self.assertEqual(execution._dispositions['domain_B' if domain == 'domain_A' else 'domain_A'], 'stale')

    def test_matching_error_with_missing_or_forged_child_event_does_not_pass(self):
        for defect in ('missing_event', 'changed_stage', 'unconsumed', 'changed_hook_world'):
            with self.subTest(defect=defect):
                execution, _ = self.child_fault_execution('F15', defect)
                with self.assertRaisesRegex(ValueError, '^lcer.fault_event_invalid$'):
                    execution.run_failure()
                self.assertIsNone(execution._failure_code)
                self.assertEqual(execution.canonical.publication_count, 1)

    def test_postcommit_world_failure_preserves_head_and_censuses_both_peers(self):
        execution, log, faults = self.execution('W1')
        faults['owner'] = ('domain_A', 'inspect_L4')
        with self.assertRaisesRegex(ValueError, '^lcer.live_owner_mismatch$'):
            execution.run_prefix('P5')
        self.assertEqual(execution.canonical.publication_count, 1)
        self.assertEqual(execution.canonical.head_raw, execution.canonical._core._r1)
        self.assertIn(('inspect', 'domain_B', 'inspect_L4', 'end'), log)
        self.assertNotIn(('materialize', 'domain_B', 'materialize_0002', 'begin'), log)
        self.assertEqual(set(execution._dispositions.values()), {'unclaimed'})

    def test_receipt_actor_must_be_the_actual_censused_actor(self):
        execution, _, faults = self.execution('W1')
        faults['receipt'] = ('domain_A', 'materialize_0002')
        with self.assertRaisesRegex(ValueError, '^lcer.materialization_receipt_invalid$'):
            execution.run_prefix('P5')
        self.assertEqual(execution.canonical.publication_count, 1)

    def test_emission_event_must_name_the_observed_resource(self):
        execution, _, faults = self.execution('W1')
        faults['actor'] = 'domain_A'
        with self.assertRaisesRegex(ValueError, '^lcer.protocol_event_mismatch$'):
            execution.run_prefix('P1')
        self.assertEqual(execution.canonical.captures()[0]['emission'], None)

    def test_original_exit_before_resolve_samples_peer_and_prevents_publication(self):
        execution, log, faults = self.execution('W1')
        faults['exit'] = ('domain_A', 'before_resolve')
        with self.assertRaisesRegex(ValueError, '^lcer.original_process_exited$'):
            execution.run_prefix('P3')
        self.assertIn(('sample', 'domain_B', 'before_resolve', 0), log)
        self.assertEqual(execution.canonical.publication_count, 0)
        self.assertEqual(len(execution.canonical._core.retained_calls()), 3)

    def test_deadline_and_changed_case_reject_before_launch(self):
        execution, log, _ = self.execution('W1')
        execution._deadline = 0
        with self.assertRaisesRegex(TimeoutError, '^lcer.case_timeout$'):
            execution.run_prefix('P0')
        self.assertEqual(log, [])
        execution, log, _ = self.execution('W2')
        execution.case['witness']['refresh'].reverse()
        with self.assertRaisesRegex(ValueError, '^lcer.case_configuration_mismatch$'):
            execution.run_prefix('P0')
        self.assertEqual(log, [])

    def test_case_records_reconcile_closed_wire_bytes_and_independent_replay(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        for name in ('W1', 'W8', 'F01', 'F03', 'F10a', 'C01'):
            with self.subTest(case=name):
                execution, _, _ = self.execution(name, artifact_wire=True)
                record = execution.execute_case()
                self.assertEqual(record['status'], 'accepted' if name.startswith('W') else 'expected_failure')
                expected_commit = name.startswith('W') or name == 'F10a'
                self.assertEqual(record['claims']['canonical_commit'], expected_commit)
                self.assertEqual(record['claims']['synchronized_representation'], name.startswith('W'))
                self.assertFalse(record['claims']['trusted_ci'])
                self.assertTrue(execution.cohort._closed)
                self.assertTrue(execution.trace.stream.closed)
                path = execution.workspace._output_root / name / 'record.json'
                self.assertEqual(path.read_bytes(), stored_json_bytes(record))
                self.assertEqual([row['path'] for row in record['artifact_sha256']], self.policy['artifact_hash_graph']['case_record_targets'][name])
                artifacts = {}
                for row in record['artifact_sha256']:
                    raw = (execution.workspace._output_root / row['path']).read_bytes()
                    self.assertEqual((hashlib.sha256(raw).hexdigest(), len(raw)), (row['sha256'], row['size_bytes']))
                    artifacts[row['path']] = raw
                artifacts[name + '/record.json'] = stored_json_bytes(record)
                for symbol in ('R0', 'R1', 'QA', 'QB'):
                    artifacts['canonical/' + symbol + '.json'] = (CONTRACT_PATH.parent / 'ConcurrentExternalEvidenceArbitrationProofRecords' / ('concurrent_external_' + symbol + '.json')).read_bytes()
                trace = verifier._trace_relations(self.policy, artifacts, record)
                verifier._operation_schedule_relations(self.policy, record, trace)
                verifier._replay_canonical(self.policy, artifacts, record, self.canonical)
                verifier._materialization_relations(self.policy, artifacts, record, trace, self.canonical)
                verifier._world_trace_relations(self.policy, artifacts, record, trace, self.canonical, self.parents)
                verifier._harness_fault_relations(self.policy, artifacts, record, trace, self.canonical)
                verifier._case_outcome_relations(self.policy, artifacts, record, trace)
                original = path.read_bytes()
                with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'):
                    execution.execute_case()
                self.assertEqual(path.read_bytes(), original)

    def test_cleanup_failure_retains_r1_and_disables_case_acceptance(self):
        execution, _, faults = self.execution('W1', artifact_wire=True)
        faults['cleanup_error'] = True
        record = execution.execute_case()
        self.assertEqual(record['status'], 'acquisition_failure')
        self.assertEqual(record['failure_codes'], ['fixture_cleanup_error'])
        self.assertFalse(record['claims']['synchronized_representation'])
        self.assertTrue(record['claims']['canonical_commit'])
        self.assertEqual(record['canonical_artifacts']['published_raw_utf8'].encode(), execution.canonical._core._r1)
        self.assertEqual(record['canonical_artifacts']['terminal_raw_utf8'], record['canonical_artifacts']['published_raw_utf8'])

    def test_unconsumed_output_prevents_record_even_after_successful_schedule(self):
        execution, _, faults = self.execution('W1', artifact_wire=True)
        faults['untraced_output'] = 'domain_A'
        with self.assertRaisesRegex(ValueError, '^lcer.untraced_process_output$'):
            execution.execute_case()
        self.assertTrue(execution.cohort._closed)
        self.assertTrue(execution.trace.stream.closed)
        self.assertFalse((execution.workspace._output_root / 'W1/record.json').exists())
        self.assertIn(b'unconsumed output', (execution.workspace._output_root / 'W1/domain_A.stdout.log').read_bytes())

    def test_extra_case_artifact_is_preserved_and_blocks_record_construction(self):
        execution, _, faults = self.execution('W1', artifact_wire=True)
        faults['artifact_extra'] = True
        with self.assertRaisesRegex(ValueError, '^lcer.case_artifact_membership_invalid$'):
            execution.execute_case()
        self.assertEqual((execution.workspace._output_root / 'W1/undeclared.bin').read_bytes(), b'extra')
        self.assertFalse((execution.workspace._output_root / 'W1/record.json').exists())


class OperationScheduleRelationTests(unittest.TestCase):
    """Actual parent/canonical execution over explicit record transports."""

    def setUp(self):
        self.fixture = CasePrefixExecutionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier, self.policy = verifier, self.fixture.policy

    def make_case(self, name='W1'):
        execution, _, _ = self.fixture.execution(name, artifact_wire=True)
        self.case = execution.execute_case()
        self.assertEqual(self.case['status'], 'accepted' if name.startswith('W') else 'expected_failure')
        self.artifacts = {row['path']: (execution.workspace._output_root / row['path']).read_bytes()
                          for row in self.case['artifact_sha256']}
        self.events = copy.deepcopy(self.case['command_trace'])
        return execution

    def sync(self, keep_clock=False):
        previous = None
        base_clock = min(row['monotonic_ns'] for row in self.events)
        for number, event in enumerate(self.events):
            event.update(sequence=number, previous_event_sha256=previous)
            if not keep_clock: event['monotonic_ns'] = base_clock + number
            previous = hashlib.sha256(stored_json_bytes(event)).hexdigest()
        self.case['command_trace'] = copy.deepcopy(self.events)
        self.case['liveness_checkpoints'] = [row['payload'] for row in self.events if row['event_id'] == 'liveness']
        self.case['head_dispositions'] = [row['payload'] for row in self.events if row['event_id'] == 'head_event']
        self.artifacts[self.case['witness_id'] + '/harness.jsonl'] = b''.join(stored_json_bytes(row) for row in self.events)

    def verify(self):
        trace = self.verifier._trace_relations(self.policy, self.artifacts, self.case)
        tokens = self.verifier._operation_schedule_relations(self.policy, self.case, trace)
        for role in ('R0', 'R1', 'QA', 'QB'):
            self.artifacts['canonical/' + role + '.json'] = (CONTRACT_PATH.parent / 'ConcurrentExternalEvidenceArbitrationProofRecords' /
                ('concurrent_external_' + role + '.json')).read_bytes()
        self.verifier._materialization_relations(self.policy, self.artifacts, self.case, trace, self.fixture.canonical)
        self.verifier._world_trace_relations(self.policy, self.artifacts, self.case, trace, self.fixture.canonical, self.fixture.parents)
        self.verifier._harness_fault_relations(self.policy, self.artifacts, self.case, trace, self.fixture.canonical)
        self.verifier._case_outcome_relations(self.policy, self.artifacts, self.case, trace)
        return tokens

    def rebuild_streams(self):
        # Materialize this explicitly mutated fixture's stream order. This
        # repairs byte offsets, never the invalid scheduling being tested.
        offsets = {}; outputs = {}
        for row in self.events:
            if row['event_id'] != 'wire_event': continue
            payload = row['payload']; key = (row['domain'], payload['direction'])
            payload['stream_byte_offset'] = offsets.get(key, 0)
            raw = payload['raw_line_utf8'].encode()
            offsets[key] = payload['stream_byte_offset'] + len(raw)
            if payload['direction'] == 'stdout': outputs[key] = outputs.get(key, b'') + raw
        for (domain, _), raw in outputs.items():
            self.artifacts[self.case['witness_id'] + '/' + domain + '.stdout.log'] = raw

    def find(self, kind, domain=None, operation=None, checkpoint=None, edge=None):
        return next(index for index, row in enumerate(self.events) if row['event_id'] == kind and
                    (domain is None or row['domain'] == domain) and
                    (operation is None or row['operation_id'] == operation) and
                    (checkpoint is None or row['payload'].get('checkpoint') == checkpoint) and
                    (edge is None or row['payload'].get('edge') == edge))

    def typed_failure_case(self, name, materialization_bytes=False):
        """Actual parent prefix, explicitly simulated process/child fault tail.

        The optional byte variant uses actual canonical materialization inputs
        and fixture receipts. Neither variant proves raw-stream, fault-action,
        physical-world or liveness acceptance.
        """
        execution, _, _ = self.fixture.execution(name, artifact_wire=True)
        execution.run_prefix(execution.case['prefix'])
        self.execution = execution
        self.events = execution.trace.rows()
        self.case = {'witness_id': name, 'process_bindings': list(execution._bindings.values())}
        program = next(row for row in self.policy['failure_programs'] if row['id'] == name)
        definitions = self.policy['wire_schemas']
        bindings = execution._bindings
        domains = ('domain_A', 'domain_B')

        def add(kind, payload, domain, operation=None):
            self.events.append({'sequence': len(self.events), 'event_id': kind, 'payload': copy.deepcopy(payload),
                                'domain': domain, 'operation_id': operation,
                                'monotonic_ns': self.events[-1]['monotonic_ns'] + 1, 'previous_event_sha256': None})

        def wire(kind, payload, domain, operation=None):
            add('wire_event', {'direction': 'stdin' if kind == 'command' else 'stdout', 'parsed_schema': kind,
                               'raw_line_utf8': stored_json_bytes(payload).decode(), 'stream_byte_offset': 0}, domain, operation)

        fault = schema_example(definitions['fault_event'], definitions)
        fault.update(failure_case=name, consumed=True, **{key: program[key] for key in ('executor', 'stage', 'action', 'underlying_code')})

        def command(kind, operation, domain, child_fault=False, failure=False):
            binding = bindings[domain]
            routing = {key: binding[key] for key in ('witness_id', 'domain', 'launch_id')}
            routing.update(operation_id=operation, binding_sha256=hashlib.sha256(stored_json_bytes(binding)).hexdigest())
            payload = (schema_example(definitions['materialize_input'], definitions) if kind == 'materialize' else
                       {'failure_case': name, 'stage': program['stage'], 'operation_id': 'materialize_0002'} if kind == 'arm_fault' else None)
            if materialization_bytes and kind == 'materialize':
                core = execution.canonical._core
                payload = execution._fault_record_input(domain, core._r0 if name == 'F17' else core._r1, 0 if name == 'F17' else 1)
                if name == 'F09':
                    initial = parse_stored_json(core._r0)
                    payload['record_raw_utf8'] = stored_json_bytes(self.fixture.canonical.working_state_projection(
                        initial, initial['current_causal_state'], initial['future_causal_state'])).decode()
                if name == 'F18': routing['binding_sha256'] = '0' * 64
            wire('command', dict(schema='city.live_evidence_command.v1', command=kind, payload=payload, **routing), domain, operation)
            if child_fault: wire('fault_event', fault, domain, operation)
            result = schema_example(definitions[self.policy['schema_contract']['response_match'][kind]], definitions)
            result.update({key: value for key, value in routing.items() if key in result})
            if kind == 'arm_fault': result.update(failure_case=name, stage=program['stage'], armed_for='materialize_0002')
            if materialization_bytes and kind == 'materialize' and not failure:
                result = execution.cohort.connection(domain).monitor.backend.request(kind, operation, payload)['response']['payload']
            error = None
            if failure:
                error = schema_example(definitions['error'], definitions)
                error['underlying_code'] = program['underlying_code']
            wire('response', dict(schema='city.live_evidence_response.v1', command=kind, **routing,
                                  status='error' if failure else 'ok', error=error, payload=None if failure else result), domain, operation)

        def sample(domain, checkpoint, exited, replacement=False):
            original = next(row['payload'] for row in self.events if row['event_id'] == 'liveness' and
                            row['domain'] == domain and row['payload']['checkpoint'] == 'startup')
            row = copy.deepcopy(original)
            row['checkpoint'] = checkpoint
            if replacement: row['launch_id'] += '_replacement'
            if exited: row.update(poll_returncode=0, observed_process=None)
            if row['observed_process'] is not None: add('process_observation', row['observed_process'], domain)
            add('liveness', row, domain)

        dead = {'F07': 'domain_A', 'F08': 'domain_B', 'F11': 'domain_A', 'F12': 'domain_B'}.get(name)
        if name == 'F08': command('emit', 'emit_0001', 'domain_A')
        if name == 'F07':
            startup = copy.deepcopy(execution.cohort.connection('domain_A').monitor.backend.startup)
            startup.update(launch_id=startup['launch_id'] + '_replacement', pid=startup['pid'] + 100)
            wire('startup', startup, 'domain_A')
        if name in ('F09', 'F17', 'F18'):
            command('materialize', 'materialize_0002', program['domain'], failure=True)
        if program['executor'] == 'unreal':
            command('arm_fault', 'arm_fault_0001', program['domain'])
            command('materialize', 'materialize_0002', program['domain'], child_fault=True, failure=name in ('F13', 'F14'))
            if name in ('F15', 'F16a', 'F16b'):
                for domain in domains: command('inspect', 'inspect_L4', domain)
        else:
            add('fault_event', fault, program['domain'])
        for domain in domains:
            if domain != dead: command('inspect', 'inspect_terminal', domain)
        for domain in domains: sample(domain, 'terminal', domain == dead)
        for domain in domains:
            add('head_event', {'edge': 'terminal', 'canonical_role': 'R1' if execution.canonical.publication_count else 'R0',
                               'canonical_raw_utf8': execution.canonical.head_raw.decode(), 'domain': domain,
                               'disposition': 'unclaimed', 'observation_sha256': None if domain == dead else 'a' * 64}, domain)
        for domain in domains:
            if domain != dead: command('shutdown', 'shutdown_0001', domain)
            sample(domain, 'cleanup', True)
        if name == 'F07': sample('domain_A', 'cleanup', True, replacement=True)
        return self.verifier._operation_schedule_relations(self.policy, self.case, {'events': self.events})

    def test_all_witness_and_canonical_failure_schedules_use_actual_parent_execution(self):
        names = [row['id'] for row in self.policy['witnesses']]
        names += [row['id'] for row in self.policy['failure_programs'] if row['underlying_code'].startswith('concurrent_external_')]
        names += ['C%02d' % number for number in range(1, 7)]
        self.assertEqual(len(names), 23)
        for name in names:
            with self.subTest(case=name):
                self.make_case(name)
                tokens = self.verify()
                self.assertTrue(tokens)

    def test_overlapping_peer_requests_fail_after_raw_transport_reconciliation(self):
        self.make_case()
        left = self.find('wire_event', 'domain_A', 'inspect_L1')
        right = self.find('wire_event', 'domain_B', 'inspect_L1')
        self.events.insert(left + 1, self.events.pop(right))
        self.sync()
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'): self.verify()

    def test_remaining_twelve_fault_tails_are_explicit_typed_schedule_fixtures(self):
        names = [row['id'] for row in self.policy['failure_programs'] if not row['underlying_code'].startswith('concurrent_external_')]
        self.assertEqual(len(names), 12)
        for name in names:
            with self.subTest(case=name): self.assertTrue(self.typed_failure_case(name))

    def test_child_fault_must_be_consumed_once_inside_the_matching_materialization(self):
        for change in ('missing', 'duplicate', 'wrong_stage', 'after_response'):
            self.typed_failure_case('F13')
            index = next(i for i, row in enumerate(self.events) if row['event_id'] == 'wire_event' and
                         row['payload']['parsed_schema'] == 'fault_event')
            if change == 'missing': self.events.pop(index)
            elif change == 'duplicate': self.events.insert(index, copy.deepcopy(self.events[index]))
            elif change == 'wrong_stage':
                payload = self.events[index]['payload']
                message = json.loads(payload['raw_line_utf8']); message['stage'] = 'wrong_stage'
                payload['raw_line_utf8'] = stored_json_bytes(message).decode()
            else: self.events[index:index + 2] = self.events[index:index + 2][::-1]
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^lcer.fault_event_invalid$'):
                self.verifier._operation_schedule_relations(self.policy, self.case, {'events': self.events})

    def test_declared_command_failure_cannot_be_replaced_with_success_or_another_code(self):
        for change in ('success', 'different_code'):
            self.typed_failure_case('F09')
            row = next(row for row in self.events if row['event_id'] == 'wire_event' and row['operation_id'] == 'materialize_0002' and
                       row['payload']['parsed_schema'] == 'response')
            message = json.loads(row['payload']['raw_line_utf8'])
            if change == 'success':
                message.update(status='ok', error=None, payload=schema_example(self.policy['wire_schemas']['materialization_result'], self.policy['wire_schemas']))
            else: message['error']['underlying_code'] = 'lcer.other_error'
            row['payload']['raw_line_utf8'] = stored_json_bytes(message).decode()
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^lcer.unexpected_failure_outcome$'):
                self.verifier._operation_schedule_relations(self.policy, self.case, {'events': self.events})

    def test_acknowledgments_bind_the_observed_startup_route_and_declared_fault(self):
        for change, code in (('startup', 'lcer.binding_mismatch'), ('route', 'lcer.protocol_response_mismatch'),
                             ('fault_stage', 'lcer.fault_arm_invalid'), ('armed_operation', 'lcer.schema_invalid')):
            self.typed_failure_case('F13')
            operation = 'bind_0001' if change == 'startup' else 'arm_fault_0001'
            row = next(row for row in self.events if row['event_id'] == 'wire_event' and row['operation_id'] == operation and
                       row['payload']['parsed_schema'] == 'response')
            message = json.loads(row['payload']['raw_line_utf8'])
            if change == 'startup': message['payload']['startup_sha256'] = 'f' * 64
            elif change == 'route': message['payload']['launch_id'] += '_changed'
            elif change == 'fault_stage': message['payload']['stage'] = 'wrong_stage'
            else: message['payload']['armed_for'] = 'materialize_0001'
            row['payload']['raw_line_utf8'] = stored_json_bytes(message).decode()
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^' + code + '$'):
                self.verifier._operation_schedule_relations(self.policy, self.case, {'events': self.events})

    def test_resolve_before_liveness_and_publish_before_return_reject(self):
        for change in ('resolve_before_sample', 'publish_before_return'):
            self.make_case()
            resolve = next(i for i, row in enumerate(self.events) if row['event_id'] == 'canonical_call' and
                           row['payload']['function'] == 'resolve_external_batch')
            if change == 'resolve_before_sample':
                target = self.find('liveness', 'domain_A', checkpoint='before_resolve') - 1
                self.events.insert(target, self.events.pop(resolve))
            else:
                publish = self.find('head_event', edge='publish')
                self.events.insert(resolve, self.events.pop(publish))
            self.sync()
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'): self.verify()

    def test_refresh_before_publication_rejects(self):
        self.make_case()
        refresh = self.find('wire_event', 'domain_A', 'materialize_0002')
        block = self.events[refresh:refresh + 2]
        del self.events[refresh:refresh + 2]
        publish = self.find('head_event', edge='publish')
        self.events[publish:publish] = block
        self.rebuild_streams()
        self.sync()
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'): self.verify()

    def test_wrong_physical_emission_order_rejects(self):
        self.make_case()
        left = self.find('wire_event', 'domain_A', 'emit_0001')
        right = self.find('wire_event', 'domain_B', 'emit_0001')
        self.assertEqual(right, left + 3)
        self.events[left:right + 3] = self.events[right:right + 3] + self.events[left:right]
        self.sync()
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'): self.verify()

    def test_head_claim_before_both_censuses_complete_rejects(self):
        self.make_case()
        head = self.find('head_event', 'domain_A', edge='classify')
        block = self.events[head:head + 2]
        del self.events[head:head + 2]
        inspect = self.find('wire_event', 'domain_B', 'inspect_L0')
        self.events[inspect + 1:inspect + 1] = block
        self.sync()
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'): self.verify()

    def test_declared_fault_cannot_precede_its_rejected_call(self):
        self.make_case('F03')
        fault = self.find('fault_event')
        rejected = self.find('canonical_call')
        self.events.insert(rejected, self.events.pop(fault))
        self.sync()
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'): self.verify()

    def test_shutdown_cannot_precede_terminal_capture(self):
        self.make_case('F03')
        shutdown = self.find('wire_event', 'domain_A', 'shutdown_0001')
        block = self.events[shutdown:shutdown + 2]
        del self.events[shutdown:shutdown + 2]
        terminal = self.find('wire_event', 'domain_A', 'inspect_terminal')
        self.events[terminal:terminal] = block
        self.rebuild_streams()
        self.sync()
        with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'): self.verify()

    def test_response_and_case_deadlines_use_recorded_monotonic_intervals(self):
        for change, code in (('operation', 'lcer.operation_timeout'), ('case', 'lcer.case_timeout')):
            self.make_case()
            index = (self.find('wire_event', 'domain_A', 'inspect_L1') + 1) if change == 'operation' else 1
            shift = (61 if change == 'operation' else 901) * 10**9
            for row in self.events[index:]: row['monotonic_ns'] += shift
            self.sync(keep_clock=True)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^' + code + '$'): self.verify()


class MaterializationRelationTests(unittest.TestCase):
    """Independent byte predicates over real parent records and explicit tails."""

    def setUp(self):
        self.fixture = OperationScheduleRelationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.verifier, self.policy = self.fixture.verifier, self.fixture.policy
        self.canonical = self.fixture.fixture.canonical
        self.canonical_artifacts = {'canonical/' + role + '.json': (CONTRACT_PATH.parent /
            'ConcurrentExternalEvidenceArbitrationProofRecords' / ('concurrent_external_' + role + '.json')).read_bytes()
            for role in ('R0', 'R1')}

    def baseline(self):
        self.fixture.make_case()
        self.original = (copy.deepcopy(self.fixture.case), copy.deepcopy(self.fixture.events), dict(self.fixture.artifacts))

    def reset(self):
        self.fixture.case, self.fixture.events, self.fixture.artifacts = copy.deepcopy(self.original)

    def message(self, kind, operation, domain='domain_A'):
        row = next(row for row in self.fixture.events if row['event_id'] == 'wire_event' and
                   row['payload']['parsed_schema'] == kind and row['operation_id'] == operation and row['domain'] == domain)
        return row, json.loads(row['payload']['raw_line_utf8'])

    def replace(self, row, message):
        row['payload']['raw_line_utf8'] = stored_json_bytes(message).decode()

    def reconcile(self):
        # Rebuild all copies affected by receipt edits. A negative must reach
        # materialization semantics, not merely a stale byte offset or list.
        self.fixture.case['materialization_receipts'] = [json.loads(row['payload']['raw_line_utf8'])['payload']
            for row in self.fixture.events if row['event_id'] == 'wire_event' and row['payload']['parsed_schema'] == 'response'
            and json.loads(row['payload']['raw_line_utf8'])['command'] == 'materialize'
            and json.loads(row['payload']['raw_line_utf8'])['status'] == 'ok']
        self.fixture.rebuild_streams()
        self.fixture.sync()
        trace = self.verifier._trace_relations(self.policy, self.fixture.artifacts, self.fixture.case)
        self.verifier._operation_schedule_relations(self.policy, self.fixture.case, trace)
        return trace

    def verify(self, trace=None):
        if trace is None: trace = self.reconcile()
        return self.verifier._materialization_relations(self.policy, self.canonical_artifacts,
                                                        self.fixture.case, trace, self.canonical)

    def test_r0_and_r1_receipts_use_their_distinct_unchanged_contracts(self):
        self.baseline()
        rows = self.verify()
        self.assertEqual([(row['domain'], row['record_role']) for row in rows],
                         [('domain_A', 'R0'), ('domain_B', 'R0'), ('domain_A', 'R1'), ('domain_B', 'R1')])
        self.assertTrue(all(row['authentication_error'] is None and row['response_error'] is None for row in rows))
        with self.assertRaises(self.canonical.RepresentationRejected):
            self.canonical.validate_launch_artifact(self.canonical_artifacts['canonical/R1.json'],
                self.canonical.stored_receipt_bytes(self.canonical.launch_receipt(self.canonical.initial_canonical_envelope())))

    def test_seven_frozen_materialization_byte_adversaries_reach_semantic_check(self):
        self.baseline()
        for change in ('removed_lf', 'second_lf', 'one_byte', 'launch_raw_hash', 'projection_owner', 'r1_launch_receipt', 'provisional'):
            with self.subTest(change=change):
                self.reset()
                operation = 'materialize_0002' if change == 'r1_launch_receipt' else 'materialize_0001'
                row, message = self.message('command', operation)
                payload = message['payload']
                if change == 'removed_lf': payload['record_raw_utf8'] = payload['record_raw_utf8'][:-1]
                elif change == 'second_lf': payload['record_raw_utf8'] += '\n'
                elif change == 'one_byte':
                    record = json.loads(payload['record_raw_utf8'])
                    original = record['identity']['scenario_id']
                    record['identity']['scenario_id'] = original[:-1] + ('X' if original[-1] != 'X' else 'Y')
                    changed = stored_json_bytes(record).decode()
                    self.assertEqual(sum(a != b for a, b in zip(changed, payload['record_raw_utf8'])), 1)
                    self.assertEqual(len(changed), len(payload['record_raw_utf8']))
                    payload['record_raw_utf8'] = changed
                elif change == 'launch_raw_hash':
                    receipt = json.loads(payload['launch_receipt_raw_utf8'])
                    self.assertIn('raw_byte_sha256', receipt)
                    receipt['raw_byte_sha256'] = '0' * 64
                    payload['launch_receipt_raw_utf8'] = stored_json_bytes(receipt).decode()
                elif change == 'projection_owner': payload['projection']['allocation_owner'] = 'domain_A'
                elif change == 'r1_launch_receipt':
                    payload['launch_receipt_raw_utf8'] = self.message('command', 'materialize_0001')[1]['payload']['launch_receipt_raw_utf8']
                else:
                    initial = self.canonical.initial_canonical_envelope()
                    payload['record_raw_utf8'] = stored_json_bytes(self.canonical.working_state_projection(
                        initial, initial['current_causal_state'], initial['future_causal_state'])).decode()
                self.replace(row, message)
                trace = self.reconcile()
                code = 'lcer.schema_invalid' if change in ('removed_lf', 'second_lf') else 'lcer.release_evidence_invalid'
                with self.assertRaisesRegex(ValueError, '^' + code + '$'): self.verify(trace)

    def test_projection_routing_and_record_metadata_are_derived(self):
        self.baseline()
        for field, value in (('witness_id', 'W2'), ('domain', 'domain_B'), ('launch_id', 'other_launch'),
                             ('operation_id', 'materialize_0001'), ('binding_sha256', '0' * 64),
                             ('record_role', 'R0'), ('record_raw_sha256', '0' * 64), ('record_canonical_hash', '0' * 64),
                             ('generation', 0), ('allocation_owner', None)):
            with self.subTest(field=field):
                self.reset()
                row, message = self.message('command', 'materialize_0002')
                message['payload']['projection'][field] = value
                self.replace(row, message)
                trace = self.reconcile()
                with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.verify(trace)

    def test_r0_acceptance_bytes_are_exact_and_cannot_claim_another_process(self):
        self.baseline()
        for change in ('removed_lf', 'second_lf', 'process', 'domain', 'extra_member', 'duplicate_member'):
            with self.subTest(change=change):
                self.reset()
                row, message = self.message('response', 'materialize_0001')
                raw = message['payload']['r0_acceptance_raw_utf8']
                receipt = json.loads(raw)
                if change == 'removed_lf': raw = raw[:-1]
                elif change == 'second_lf': raw += '\n'
                elif change == 'duplicate_member': raw = '{"receipt_schema":' + json.dumps(receipt['receipt_schema']) + ',' + raw[1:]
                else:
                    receipt['process_instance_id' if change == 'process' else 'materialization_domain' if change == 'domain' else 'extra'] = (
                        'other_launch' if change == 'process' else 'domain_B' if change == 'domain' else True)
                    raw = stored_json_bytes(receipt).decode()
                message['payload']['r0_acceptance_raw_utf8'] = raw
                self.replace(row, message)
                trace = self.reconcile()
                code = 'lcer.schema_invalid' if change in ('duplicate_member', 'removed_lf', 'second_lf') else 'lcer.release_evidence_invalid'
                with self.assertRaisesRegex(ValueError, '^' + code + '$'): self.verify(trace)

    def test_receipt_kind_cannot_be_swapped_mixed_or_omitted(self):
        self.baseline()
        first = self.message('response', 'materialize_0001')[1]['payload']
        second = self.message('response', 'materialize_0002')[1]['payload']
        for operation in ('materialize_0001', 'materialize_0002'):
            for change in ('swap', 'both', 'neither'):
                with self.subTest(operation=operation, change=change):
                    self.reset()
                    row, message = self.message('response', operation)
                    message['payload'] = (copy.deepcopy(second if operation == 'materialize_0001' else first) if change == 'swap' else
                        {'r0_acceptance_raw_utf8': first['r0_acceptance_raw_utf8'] if change == 'both' else None,
                         'r1_representation': copy.deepcopy(second['r1_representation']) if change == 'both' else None})
                    self.replace(row, message)
                    trace = self.reconcile()
                    with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.verify(trace)

    def test_r1_receipt_metadata_and_actor_distinction_are_checked(self):
        self.baseline()
        for field, value in (('witness_id', 'W2'), ('domain', 'domain_B'), ('launch_id', 'other_launch'),
                             ('operation_id', 'materialize_0001'), ('binding_sha256', '0' * 64),
                             ('record_raw_sha256', '0' * 64), ('record_canonical_hash', '0' * 64), ('anchor_actor_id', None)):
            with self.subTest(field=field):
                self.reset()
                row, message = self.message('response', 'materialize_0002')
                receipt = message['payload']['r1_representation']
                receipt[field] = value if value is not None else receipt['resource_actor_id']
                self.replace(row, message)
                trace = self.reconcile()
                with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.verify(trace)

    def test_raw_json_strings_cannot_hide_duplicate_or_extra_members(self):
        self.baseline()
        for target in ('record_raw_utf8', 'launch_receipt_raw_utf8'):
            for change in ('duplicate', 'extra'):
                with self.subTest(target=target, change=change):
                    self.reset()
                    row, message = self.message('command', 'materialize_0001')
                    raw = message['payload'][target]
                    parsed = json.loads(raw)
                    key = next(iter(parsed))
                    if change == 'duplicate': raw = '{' + json.dumps(key) + ':' + json.dumps(parsed[key]) + ',' + raw[1:]
                    else: raw = stored_json_bytes(dict(parsed, extra=True)).decode()
                    message['payload'][target] = raw
                    self.replace(row, message)
                    trace = self.reconcile()
                    code = 'lcer.schema_invalid' if change == 'duplicate' else 'lcer.release_evidence_invalid'
                    with self.assertRaisesRegex(ValueError, '^' + code + '$'): self.verify(trace)

    def test_twelve_typed_fault_tails_check_materialization_bytes_only(self):
        for program in self.policy['failure_programs']:
            if program['underlying_code'].startswith('concurrent_external_'): continue
            name = program['id']
            with self.subTest(case=name):
                self.fixture.typed_failure_case(name, materialization_bytes=True)
                rows = self.verify({'events': self.fixture.events})
                failed = [row for row in rows if row['response_error'] is not None]
                self.assertEqual(len(failed), int(name in ('F09', 'F13', 'F14', 'F17', 'F18')))
                if failed:
                    self.assertEqual(failed[0]['response_error'], program['underlying_code'])
                    self.assertEqual(failed[0]['authentication_error'], program['underlying_code'] if name in ('F09', 'F17', 'F18') else None)

    def test_expected_rejection_code_does_not_excuse_a_different_invalid_command(self):
        for name in ('F09', 'F17', 'F18'):
            self.fixture.typed_failure_case(name, materialization_bytes=True)
            original = copy.deepcopy(self.fixture.events)
            for change in ('raw_bytes', 'projection', 'lexical_number'):
                with self.subTest(case=name, change=change):
                    self.fixture.events = copy.deepcopy(original)
                    row, message = self.message('command', 'materialize_0002')
                    if change == 'raw_bytes': message['payload']['record_raw_utf8'] += '\n'
                    elif change == 'projection': message['payload']['projection']['record_canonical_hash'] = '0' * 64
                    else: message['payload']['projection']['generation'] = float(message['payload']['projection']['generation'])
                    self.replace(row, message)
                    # The transport/schedule tail remains explicitly synthetic.
                    self.verifier._operation_schedule_relations(self.policy, self.fixture.case, {'events': self.fixture.events})
                    code = 'lcer.schema_invalid' if change == 'raw_bytes' and name != 'F18' else 'lcer.release_evidence_invalid'
                    with self.assertRaisesRegex(ValueError, '^' + code + '$'):
                        self.verify({'events': self.fixture.events})


class WorldTraceRelationTests(unittest.TestCase):
    """Census/receipt joins over record transports and explicitly typed faults."""

    def setUp(self):
        self.material = MaterializationRelationTests()
        self.material.setUp()
        self.addCleanup(self.material.doCleanups)
        self.fixture = self.material.fixture
        self.verifier, self.policy, self.canonical = self.material.verifier, self.material.policy, self.material.canonical
        self.parents = self.fixture.fixture.parents
        self.artifacts = dict(self.material.canonical_artifacts)
        for role in ('QA', 'QB'):
            self.artifacts['canonical/' + role + '.json'] = (CONTRACT_PATH.parent /
                'ConcurrentExternalEvidenceArbitrationProofRecords' / ('concurrent_external_' + role + '.json')).read_bytes()

    def verify(self, trace):
        return self.verifier._world_trace_relations(self.policy, self.artifacts, self.fixture.case,
                                                    trace, self.canonical, self.parents)

    def reconcile(self):
        observations, captures = [], {}
        for row in self.fixture.events:
            if row['event_id'] != 'wire_event' or row['payload']['parsed_schema'] != 'response': continue
            message = json.loads(row['payload']['raw_line_utf8'])
            if message['status'] != 'ok': continue
            if message['command'] == 'inspect': observations.append(message['payload'])
            if message['command'] == 'emit': captures[message['domain']] = message['payload']
        self.fixture.case['live_observations'] = observations
        for slot in self.fixture.case['captured_evidence']: slot['emission'] = captures.get(slot['domain'])
        trace = self.material.reconcile()
        self.material.verify(trace)
        return trace

    def redraw(self, observation):
        for world in observation['worlds']:
            world['actors'].sort(key=lambda row: row['actor_path'])
            size = len(world['actors'])
            world.update(actor_array_size=size, visited_slots=list(range(size)), null_slots=[])
        observation.update(self.verifier._world_facts(self.policy, observation['worlds'], self.parents)['summary'])

    def test_receipt_actor_ids_must_match_the_independent_census(self):
        self.material.baseline()
        for field in ('anchor_actor_id', 'resource_actor_id'):
            with self.subTest(field=field):
                self.material.reset()
                row, message = self.material.message('response', 'materialize_0002')
                message['payload']['r1_representation'][field] += '_forged'
                self.material.replace(row, message)
                trace = self.reconcile()
                with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.verify(trace)

    def test_changed_world_facts_reject_even_with_matching_summary(self):
        self.material.baseline()
        for change in ('owner', 'generation', 'record', 'domain', 'missing_anchor', 'extra_resource', 'pending_kill', 'input'):
            with self.subTest(change=change):
                self.material.reset()
                row, message = self.material.message('response', 'inspect_L4')
                observation = message['payload']; actors = observation['worlds'][0]['actors']
                resource = next(actor for actor in actors if actor['role'] == 'resource_state')
                if change == 'owner': resource['allocation_owner'] = 'domain_B'
                elif change == 'generation': resource['generation'] = 0
                elif change == 'record': resource['record_raw_sha256'] = '0' * 64
                elif change == 'domain': resource['domain'] = 'domain_B'
                elif change == 'missing_anchor': actors[:] = [actor for actor in actors if actor['role'] != 'head_anchor']
                elif change == 'extra_resource':
                    extra = dict(resource, actor_path=resource['actor_path'] + '_extra', actor_id=resource['actor_id'] + '_extra')
                    actors.append(extra)
                elif change == 'pending_kill': resource['pending_kill'] = True
                else: resource['auto_receive_input'] = 1
                self.redraw(observation)
                self.material.replace(row, message)
                trace = self.reconcile()
                with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.verify(trace)

    def test_head_claims_are_recomputed_from_canonical_and_observed_bytes(self):
        self.material.baseline()
        for change in ('owner_head', 'wrong_role', 'stale_claim', 'false_current', 'wrong_observation', 'missing_observation'):
            with self.subTest(change=change):
                self.material.reset()
                row = next(row for row in self.fixture.events if row['event_id'] == 'head_event' and
                           row['payload']['edge'] == 'classify' and row['domain'] == 'domain_A' and
                           (row['payload']['observation_sha256'] is None if change == 'false_current' else
                            row['payload']['observation_sha256'] is not None))
                head = row['payload']
                if change == 'owner_head': head['canonical_raw_utf8'] = self.artifacts['canonical/R1.json'].decode()
                elif change == 'wrong_role': head['canonical_role'] = 'R1'
                elif change == 'stale_claim': head['disposition'] = 'stale'
                elif change == 'false_current': head['disposition'] = 'current'
                elif change == 'wrong_observation': head['observation_sha256'] = '0' * 64
                else: head['observation_sha256'] = None
                if change == 'missing_observation':
                    with self.assertRaisesRegex(ValueError, '^lcer.operation_sequence_invalid$'): self.reconcile()
                    continue
                trace = self.reconcile()
                with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.verify(trace)

    def test_emission_must_bind_the_observed_resource_and_unchanged_receipts(self):
        self.material.baseline()
        for change in ('actor', 'q', 'wrapper', 'acceptance', 'emission', 'counter'):
            with self.subTest(change=change):
                self.material.reset()
                row, message = self.material.message('response', 'emit_0001')
                result = message['payload']
                if change == 'actor': result['physical_event']['actor_id'] += '_forged'
                elif change == 'q': result['q_raw_utf8'] = self.artifacts['canonical/QB.json'].decode()
                elif change == 'wrapper': result['wrapper']['source_record_hash'] = '0' * 64
                elif change == 'counter': result['physical_event']['interaction_counter'] = 2
                else:
                    field = 'acceptance_receipt_raw_utf8' if change == 'acceptance' else 'emission_receipt_raw_utf8'
                    receipt = json.loads(result[field]); receipt['process_instance_id'] = 'forged_launch'
                    result[field] = stored_json_bytes(receipt).decode()
                self.material.replace(row, message)
                physical_row, _ = self.material.message('physical_event', 'emit_0001')
                self.material.replace(physical_row, result['physical_event'])
                if change == 'counter':
                    with self.assertRaisesRegex(ValueError, '^lcer.schema_invalid$'): self.reconcile()
                    continue
                trace = self.reconcile()
                with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.verify(trace)

    def child_case(self, name):
        # Splice explicit world fixtures into the typed scheduling tail. These
        # worlds are produced by the existing parent fault fixture, not Unreal.
        self.fixture.typed_failure_case(name, materialization_bytes=True)
        execution, _ = self.fixture.fixture.child_fault_execution(name)
        execution.run_failure()
        fault = copy.deepcopy(execution._wire_faults[0])
        domain = execution.case['failure_program']['domain']
        binding = next(row for row in self.fixture.case['process_bindings'] if row['domain'] == domain)
        for side in ('before', 'after'):
            observation = fault[side]['observation']
            observation.update({field: binding[field] for field in ('witness_id', 'domain', 'launch_id')})
            observation['binding_sha256'] = hashlib.sha256(stored_json_bytes(binding)).hexdigest()
        latest = {}
        for row in self.fixture.events:
            if row['event_id'] != 'wire_event': continue
            kind = row['payload']['parsed_schema']
            if kind == 'fault_event': self.material.replace(row, fault)
            if kind != 'response': continue
            message = json.loads(row['payload']['raw_line_utf8'])
            if message['command'] != 'inspect': continue
            operation = message['operation_id']; peer = row['domain']
            if operation in ('inspect_L4', 'inspect_terminal'):
                message['payload'] = copy.deepcopy(fault['after']['observation'] if peer == domain else latest[peer])
                message['payload']['operation_id'] = operation
                self.material.replace(row, message)
            latest[peer] = message['payload']
        for row in self.fixture.events:
            if row['event_id'] == 'head_event' and row['payload']['edge'] == 'terminal':
                peer = row['domain']
                row['payload']['disposition'] = ('unavailable' if name in ('F13', 'F14') else 'unclaimed') if peer == domain else 'stale'
                row['payload']['observation_sha256'] = hashlib.sha256(stored_json_bytes(latest[peer])).hexdigest()
        trace = {'events': self.fixture.events}
        self.verifier._operation_schedule_relations(self.policy, self.fixture.case, trace)
        self.material.verify(trace)
        return trace, domain

    def test_all_five_typed_child_world_tails_have_exact_physical_effects(self):
        for name in ('F13', 'F14', 'F15', 'F16a', 'F16b'):
            with self.subTest(case=name):
                trace, domain = self.child_case(name)
                result = self.verify(trace)
                self.assertEqual(result['child_effects'], [domain])
                self.assertEqual(result['terminal_dispositions'][domain], 'unavailable' if name in ('F13', 'F14') else 'unclaimed')
                self.assertEqual(result['terminal_dispositions']['domain_B' if domain == 'domain_A' else 'domain_A'], 'stale')

    def test_partial_world_cannot_restore_r0_or_publish_an_anchor(self):
        for change in ('restored_r0', 'anchor'):
            with self.subTest(change=change):
                trace, domain = self.child_case('F13')
                row, message = self.material.message('response', 'inspect_terminal', domain)
                observation = message['payload']
                if change == 'restored_r0':
                    observation['worlds'] = copy.deepcopy(self.material.message('response', 'inspect_L3', domain)[1]['payload']['worlds'])
                else:
                    anchor = copy.deepcopy(next(actor for actor in self.material.message('response', 'inspect_L3', domain)[1]['payload']['worlds'][0]['actors']
                                                if actor['role'] == 'head_anchor'))
                    anchor.update(generation=1, record_raw_sha256=hashlib.sha256(self.artifacts['canonical/R1.json']).hexdigest())
                    observation['worlds'][0]['actors'].append(anchor)
                self.redraw(observation)
                self.material.replace(row, message)
                with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.verify(trace)

    def test_fault_cannot_change_an_unrelated_actor_or_the_truthful_receipt(self):
        for change in ('unrelated_actor', 'receipt'):
            with self.subTest(change=change):
                trace, domain = self.child_case('F15')
                if change == 'unrelated_actor':
                    row, fault = self.material.message('fault_event', 'materialize_0002', domain)
                    controller = next(actor for actor in fault['after']['observation']['worlds'][0]['actors'] if actor['role'] is None)
                    controller['pending_kill'] = True
                    self.material.replace(row, fault)
                else:
                    row, message = self.material.message('response', 'materialize_0002', domain)
                    message['payload']['r1_representation']['anchor_actor_id'] += '_forged'
                    self.material.replace(row, message)
                    self.material.verify(trace)
                with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.verify(trace)

    def test_extra_resource_fault_keeps_old_rows_and_exact_new_generation(self):
        for name in ('F16a', 'F16b'):
            trace, domain = self.child_case(name)
            original = copy.deepcopy(self.fixture.events)
            for change in ('old_actor', 'new_generation', 'new_owner', 'new_record', 'world_context'):
                with self.subTest(case=name, change=change):
                    self.fixture.events = copy.deepcopy(original)
                    trace = {'events': self.fixture.events}
                    row, fault = self.material.message('fault_event', 'materialize_0002', domain)
                    after = fault['after']['observation']
                    old_ids = {actor['actor_id'] for world in fault['before']['observation']['worlds'] for actor in world['actors']}
                    actors = after['worlds'][0]['actors']
                    extra = next(actor for actor in actors if actor['actor_id'] not in old_ids)
                    if change == 'old_actor': next(actor for actor in actors if actor['role'] == 'head_anchor')['pending_kill'] = True
                    elif change == 'new_generation': extra['generation'] = 1 - extra['generation']
                    elif change == 'new_owner': extra['allocation_owner'] = 'domain_B'
                    elif change == 'new_record': extra['record_raw_sha256'] = '0' * 64
                    else: after['worlds'][0]['game_mode_class'] = '/Script/Engine.GameModeBase'
                    self.redraw(after)
                    self.material.replace(row, fault)
                    with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.verify(trace)


class CommandBindingRelationTests(unittest.TestCase):
    """A self-consistent response pair cannot replace the original binding."""

    def setUp(self):
        self.world = WorldTraceRelationTests()
        self.world.setUp()
        self.addCleanup(self.world.doCleanups)
        self.fixture = self.world.fixture
        self.verifier, self.policy = self.world.verifier, self.world.policy

    def change_binding(self, operation, value):
        for row in self.fixture.events:
            if row['event_id'] != 'wire_event' or row['domain'] != 'domain_A' or row['operation_id'] != operation: continue
            message = json.loads(row['payload']['raw_line_utf8'])
            message['binding_sha256'] = value
            result = message.get('payload')
            if row['payload']['parsed_schema'] == 'response' and result is not None:
                if 'binding_sha256' in result: result['binding_sha256'] = value
                for field in ('physical_event', 'wrapper'):
                    if field in result: result[field]['binding_sha256'] = value
            self.world.material.replace(row, message)

    def test_all_nonmaterialization_commands_require_the_original_digest(self):
        self.world.material.baseline()
        for operation in ('bind_0001', 'emit_0001', 'inspect_L0', 'shutdown_0001'):
            with self.subTest(operation=operation):
                self.world.material.reset()
                self.change_binding(operation, '0' * 64)
                with self.assertRaisesRegex(ValueError, '^lcer.binding_mismatch$'): self.world.reconcile()

    def typed_trace(self, name):
        # Reconcile the synthetic suffix's actual encoded streams. Native
        # world and fault-action authenticity remain explicitly outside this test.
        self.fixture.typed_failure_case(name, materialization_bytes=True)
        self.fixture.artifacts = {name + '/' + domain + '.stderr.log': b'typed route fixture\n' for domain in ('domain_A', 'domain_B')}
        self.fixture.case['captured_evidence'] = [{'domain': domain, 'emission': None} for domain in ('domain_A', 'domain_B')]
        return self.world.reconcile()

    def test_frozen_f18_digest_is_the_only_declared_exception(self):
        self.typed_trace('F18')
        original = copy.deepcopy(self.fixture.events)
        binding = next(row for row in self.fixture.case['process_bindings'] if row['domain'] == 'domain_A')
        for value in (hashlib.sha256(stored_json_bytes(binding)).hexdigest(), 'f' * 64):
            with self.subTest(digest=value):
                self.fixture.events = copy.deepcopy(original)
                self.change_binding('materialize_0002', value)
                with self.assertRaisesRegex(ValueError, '^lcer.binding_mismatch$'): self.world.reconcile()

    def test_child_fault_arm_also_requires_the_original_binding(self):
        self.typed_trace('F13')
        self.change_binding('arm_fault_0001', '0' * 64)
        with self.assertRaisesRegex(ValueError, '^lcer.binding_mismatch$'): self.world.reconcile()


class HarnessFaultRelationTests(unittest.TestCase):
    """Byte snapshot and process joins; typed process inputs are not live proof."""

    def setUp(self):
        self.fixture = OperationScheduleRelationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.verifier, self.policy = self.fixture.verifier, self.fixture.policy
        self.canonical = self.fixture.fixture.canonical
        self.artifacts = {'canonical/' + role + '.json': (CONTRACT_PATH.parent /
            'ConcurrentExternalEvidenceArbitrationProofRecords' / ('concurrent_external_' + role + '.json')).read_bytes()
            for role in ('R0', 'R1', 'QA', 'QB')}

    def check(self, trace=None):
        if trace is None:
            self.fixture.sync()
            trace = self.verifier._trace_relations(self.policy, self.fixture.artifacts, self.fixture.case)
            self.verifier._operation_schedule_relations(self.policy, self.fixture.case, trace)
            self.verifier._replay_canonical(self.policy, self.artifacts, self.fixture.case, self.canonical)
        return self.verifier._harness_fault_relations(self.policy, self.artifacts, self.fixture.case, trace, self.canonical)

    def test_argument_snapshots_cannot_disagree_with_checked_parent_calls(self):
        for name in ('F01', 'F03', 'F04a', 'F04b', 'F10b'):
            self.fixture.make_case(name)
            expected = next(row['underlying_code'] for row in self.policy['failure_programs'] if row['id'] == name)
            self.assertEqual(self.check(), expected)
            original = copy.deepcopy(self.fixture.events)
            for change in ('before', 'after', 'semantic_type'):
                with self.subTest(case=name, change=change):
                    self.fixture.events = copy.deepcopy(original)
                    fault = next(row['payload'] for row in self.fixture.events if row['event_id'] == 'fault_event')
                    if change == 'semantic_type': fault['after']['semantic_type'] = 'q_raw'
                    else: fault[change]['raw_base64'] = base64.b64encode(b'{}\n').decode()
                    with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.check()

    def test_materialize_fault_snapshots_keep_original_and_exact_wire_commands(self):
        for name in ('F09', 'F17', 'F18'):
            self.fixture.typed_failure_case(name, materialization_bytes=True)
            execution = self.fixture.execution
            domain = execution.case['failure_program']['domain']
            before = execution._materialize_command_bytes(domain, execution._fault_record_input(domain, execution.canonical._core._r1, 1))
            after = next(row['payload']['raw_line_utf8'].encode() for row in self.fixture.events if row['event_id'] == 'wire_event' and
                         row['domain'] == domain and row['operation_id'] == 'materialize_0002' and row['payload']['parsed_schema'] == 'command')
            row = next(row for row in self.fixture.events if row['event_id'] == 'fault_event')
            row['operation_id'] = 'materialize_0002'
            row['payload'].update(before=execution._fault_bytes('materialize_command', before),
                                  after=execution._fault_bytes('materialize_command', after))
            trace = {'events': self.fixture.events}
            self.assertEqual(self.check(trace), execution.case['failure_program']['underlying_code'])
            original = copy.deepcopy(row['payload'])
            for side in ('before', 'after'):
                with self.subTest(case=name, side=side):
                    row['payload'] = copy.deepcopy(original)
                    row['payload'][side]['raw_base64'] = base64.b64encode((before if side == 'before' else after) + b'\n').decode()
                    with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.check(trace)

    def process_case(self, name):
        fixture = LivenessTraceRelationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.make_case(name)
        program = next(row for row in self.policy['failure_programs'] if row['id'] == name)
        if name != 'F07':
            index = 0 if program['domain'] == 'domain_A' else 1
            before = dict(copy.deepcopy(fixture.templates[index]), checkpoint='terminal')
            after = next(copy.deepcopy(row['payload']) for row in fixture.events if row['event_id'] == 'liveness' and
                         row['domain'] == program['domain'] and row['payload']['checkpoint'] == 'terminal')
            fault = {key: program[key] for key in ('executor', 'stage', 'action', 'underlying_code')}
            fault.update(failure_case=name, consumed=True, before={'kind': 'process', 'sample': before},
                         after={'kind': 'process', 'sample': after})
            fixture.add('fault_event', fault, program['domain'])
            event = fixture.events.pop()
            position = next(index for index, row in enumerate(fixture.events) if row['event_id'] == 'liveness' and row['payload']['checkpoint'] == 'terminal')
            if fixture.events[position - 1]['event_id'] == 'process_observation': position -= 1
            fixture.events.insert(position, event)
            fixture.sync()
        fixture.verify()
        self.fixture.case, self.fixture.events = fixture.case, fixture.events
        return {'events': self.fixture.events}, program

    def test_four_typed_process_faults_preserve_original_identity_and_observed_exit(self):
        for name in ('F07', 'F08', 'F11', 'F12'):
            with self.subTest(case=name):
                trace, program = self.process_case(name)
                self.assertEqual(self.check(trace), program['underlying_code'])

    def test_process_fault_snapshot_cannot_forge_before_identity_death_or_holders(self):
        for name in ('F07', 'F08', 'F11', 'F12'):
            trace, _ = self.process_case(name)
            row = next(row for row in self.fixture.events if row['event_id'] == 'fault_event')
            original = copy.deepcopy(row['payload'])
            for change, code in (('pid', 'lcer.original_process_identity_mismatch'), ('dead_before', 'lcer.release_evidence_invalid'),
                                 ('after', 'lcer.release_evidence_invalid'), ('holder', 'lcer.proof_pipe_extra_holder')):
                with self.subTest(case=name, change=change):
                    row['payload'] = copy.deepcopy(original)
                    before = row['payload']['before']['sample']; after = row['payload']['after']['sample']
                    if change == 'pid': before['observed_process']['pid'] += 999
                    elif change == 'dead_before': before.update(poll_returncode=-15, observed_process=None)
                    elif change == 'after':
                        if name == 'F07': after['launch_id'] = before['launch_id']
                        else: after['poll_returncode'] = 0
                    else:
                        extra = dict(before['pipe_holders'][0]); extra['pid'] += 999
                        before['pipe_holders'].append(extra)
                    with self.assertRaisesRegex(ValueError, '^' + code + '$'): self.check(trace)


class CaseOutcomeRelationTests(unittest.TestCase):
    """Derive envelope fields from checked records, never from success labels."""

    def setUp(self):
        self.fixture = OperationScheduleRelationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.verifier, self.policy = self.fixture.verifier, self.fixture.policy

    def baseline(self, name):
        self.fixture.make_case(name)
        self.fixture.verify()
        self.trace = self.verifier._trace_relations(self.policy, self.fixture.artifacts, self.fixture.case)
        return self.check()

    def check(self):
        return self.verifier._case_outcome_relations(self.policy, self.fixture.artifacts, self.fixture.case, self.trace)

    def complete_protocol(self):
        return self.verifier._case_protocol_relations(self.policy, self.fixture.artifacts, self.fixture.case,
            self.fixture.fixture.canonical, self.fixture.fixture.parents)

    def test_status_and_claims_cannot_override_the_observed_case(self):
        for name in ('W1', 'F03', 'F10a', 'C01'):
            expected = self.baseline(name)
            original = copy.deepcopy(self.fixture.case)
            for change in ('status', 'acquisition_failure', 'synchronized_representation', 'canonical_commit',
                           'production_ready', 'trusted_ci', 'game_sealed'):
                with self.subTest(case=name, change=change):
                    self.fixture.case = copy.deepcopy(original)
                    if change == 'status':
                        self.fixture.case['status'] = 'expected_failure' if expected['status'] == 'accepted' else 'accepted'
                    elif change == 'acquisition_failure': self.fixture.case['status'] = change
                    else: self.fixture.case['claims'][change] = not expected['claims'][change]
                    code = 'lcer.schema_invalid' if change in ('production_ready', 'trusted_ci', 'game_sealed') else 'lcer.release_evidence_invalid'
                    with self.assertRaisesRegex(ValueError, '^' + code + '$'): self.check()

    def test_failure_list_must_have_the_exact_frozen_normalization(self):
        for name in ('W1', 'F01', 'F04b', 'F10b', 'C06'):
            expected = self.baseline(name)
            original = copy.deepcopy(self.fixture.case)
            wrong = [['LCER_PROCESS_INVALID'], expected['failure_codes'] * 2] if expected['failure_codes'] else [['LCER_PROCESS_INVALID']]
            if expected['failure_codes']: wrong.append([])
            for codes in wrong:
                with self.subTest(case=name, codes=codes):
                    self.fixture.case = copy.deepcopy(original)
                    self.fixture.case['failure_codes'] = codes
                    with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.check()

    def test_changed_terminal_heads_cannot_keep_the_old_claims(self):
        for name in ('W1', 'F03'):
            with self.subTest(case=name):
                self.baseline(name)
                row = next(row for row in reversed(self.trace['events']) if row['event_id'] == 'head_event' and row['domain'] == 'domain_A')
                row['payload']['disposition'] = 'stale' if name == 'W1' else 'current'
                with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.check()

    def test_missing_duplicate_or_live_cleanup_cannot_preserve_success(self):
        self.baseline('W1')
        original = copy.deepcopy(self.trace)
        for change in ('missing', 'duplicate', 'still_live'):
            with self.subTest(change=change):
                self.trace = copy.deepcopy(original)
                index = next(index for index, row in enumerate(self.trace['events']) if row['event_id'] == 'liveness' and row['payload']['checkpoint'] == 'cleanup')
                if change == 'missing': self.trace['events'].pop(index)
                elif change == 'duplicate': self.trace['events'].append(copy.deepcopy(self.trace['events'][index]))
                else: self.trace['events'][index]['payload']['poll_returncode'] = None
                with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'): self.check()

    def test_complete_protocol_refuses_transport_fixtures_without_kernel_pipe_evidence(self):
        self.baseline('W1')
        self.assertEqual(self.fixture.case['status'], 'accepted')
        with self.assertRaisesRegex(ValueError, '^lcer.original_pipe_identity_mismatch$'):
            self.complete_protocol()


class LiveWorldAcceptanceTests(unittest.TestCase):
    """The parent independently checks fixture rows; no authenticated graph claim."""

    def setUp(self):
        self.fixture = WorldOracleTests()
        self.fixture.setUp()
        self.world = LiveWorldAcceptance(CONTRACT_PATH.read_bytes(), self.fixture.class_parents)

    def observation(self, actors):
        facts = self.fixture.census(actors)
        definitions = self.fixture.policy['wire_schemas']
        result = schema_example(definitions['live_observation'], definitions)
        result.update(facts['summary'], worlds=[copy.deepcopy(self.fixture.world)], domain='domain_A')
        return result

    def test_raw_rows_control_precedence_even_with_rehashed_summaries(self):
        anchor = self.fixture.actor('Anchor', 'head_anchor', 1)
        resource = self.fixture.actor('Resource', 'resource_state', 1, 'domain_A')
        variants = [(None, [anchor, resource]),
                    ('lcer.live_generation_mismatch', [anchor, resource, self.fixture.actor('Old', 'resource_state', 0)]),
                    ('lcer.live_actor_cardinality_mismatch', [anchor, resource, self.fixture.actor('Extra', 'resource_state', 1, 'domain_A')]),
                    ('lcer.live_owner_mismatch', [anchor, dict(resource, allocation_owner='domain_B')]),
                    ('lcer.live_actor_cardinality_mismatch', [anchor, dict(resource, pending_kill=True)]),
                    ('lcer.live_record_domain_mismatch', [anchor, dict(resource, domain='domain_B')])]
        for code, actors in variants:
            with self.subTest(code=code):
                observation = self.observation(actors)
                if code is None:
                    self.world.representation(observation, self.fixture.raw1, 1, 'domain_A')
                else:
                    with self.assertRaisesRegex(ValueError, '^' + code + '$'):
                        self.world.representation(observation, self.fixture.raw1, 1, 'domain_A')

    def test_missing_unknown_and_cyclic_class_ancestry_cannot_be_harmless(self):
        actor = self.fixture.actor('Native', class_path='/Script/Engine.Actor')
        observation = self.observation([actor])
        for parents in ({}, {'/Script/Engine.Actor': '/Script/Engine.Actor'}, {'/Script/Engine.Actor': '/Script/Engine.Missing'}):
            with self.subTest(parents=parents):
                world = LiveWorldAcceptance(CONTRACT_PATH.read_bytes(), parents)
                with self.assertRaisesRegex(ValueError, '^lcer.class_hierarchy_invalid$'):
                    world.census(observation['worlds'])

    def test_incomplete_and_duplicate_slots_reject_before_summary_acceptance(self):
        original = self.observation([self.fixture.actor('Anchor', 'head_anchor', 1), self.fixture.actor('Resource', 'resource_state', 1, 'domain_A')])
        for defect in ('omitted', 'duplicate', 'missing', 'null'):
            observation = copy.deepcopy(original)
            world = observation['worlds'][0]
            if defect == 'omitted': world['actors'].pop()
            if defect == 'duplicate': world['visited_slots'].append(0)
            if defect == 'missing': world['visited_slots'].pop()
            if defect == 'null': world['null_slots'].append(world['actor_array_size'])
            with self.subTest(defect=defect):
                with self.assertRaisesRegex(ValueError, '^lcer.world_census_invalid$'):
                    self.world.representation(observation, self.fixture.raw1, 1, 'domain_A')

    def test_startup_rejects_an_unpossessed_pawn_and_second_game_world(self):
        fixture = ProcessBindingRelationTests()
        fixture.setUp()
        self.world.startup(fixture.startup)
        pawn = self.fixture.actor('Unpossessed', class_path='/Script/Engine.Character')
        changed = copy.deepcopy(fixture.startup)
        world = changed['worlds'][0]
        world['actors'].append(pawn)
        world['actors'].sort(key=lambda row: row['actor_path'])
        world['actor_array_size'] += 1
        world['visited_slots'].append(2)
        with self.assertRaisesRegex(ValueError, '^lcer.startup_world_invalid$'):
            self.world.startup(changed)
        changed = copy.deepcopy(fixture.startup)
        other = copy.deepcopy(changed['worlds'][0])
        other.update(world_path='/Engine/Maps/Other.Other', actors=[], actor_array_size=0, visited_slots=[], null_slots=[])
        changed['worlds'].append(other)
        with self.assertRaisesRegex(ValueError, '^lcer.startup_world_invalid$'):
            self.world.startup(changed)


class CppCommandAuthorityTests(unittest.TestCase):
    """Actual compiler calls in temporary C++; no complete source-audit claim."""

    SOURCE = '''
struct ACityLiveEvidenceResource { bool Interact(int) { return true; } };
struct ACityLiveEvidenceGameMode {
    ACityLiveEvidenceResource Resource;
    void EnqueueInput(int) {}
    void Dispatch(int line) { Resource.Interact(line); }
    virtual void Tick(float) { Dispatch(1); }
    void Helper() { Tick(0); }
    void RestartPlayer(void *player) { (void)player; }
};
struct FLCERInputThread {
    ACityLiveEvidenceGameMode *Owner;
    unsigned Run() { Owner->EnqueueInput(1); return 0; }
};
'''

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier
        temporary = tempfile.TemporaryDirectory(prefix='city-command-authority-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name); self.path = self.root / 'commands.cpp'
        self.argv = ['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang',
                     '-x', 'c++', '-std=c++20', '-fsyntax-only']

    def check(self, source):
        self.path.write_text(source)
        raw = self.path.read_bytes()
        inventory = self.verifier.ClangSourceInventory().parse(self.path, [str(self.path)], self.argv)
        self.assertEqual(inventory['diagnostics'], [])
        self.assertEqual(inventory['visitor_errors'], [])
        return self.verifier.CppCommandAuthority([inventory], {str(self.path): raw}).check()

    def test_actual_worker_tick_and_dispatch_identities_are_retained(self):
        result = self.check(self.SOURCE)
        self.assertEqual(len(result['roles']), 6)
        self.assertEqual({(row['function'], row['callee']) for row in result['edges']}, {
            ('FLCERInputThread::Run', 'ACityLiveEvidenceGameMode::EnqueueInput'),
            ('ACityLiveEvidenceGameMode::Tick', 'ACityLiveEvidenceGameMode::Dispatch'),
            ('ACityLiveEvidenceGameMode::Dispatch', 'ACityLiveEvidenceResource::Interact')})
        self.assertEqual(result['unclassified'], [])
        # This deliberately small fixture checks callers only. Its constant
        # queue input cannot satisfy the independent stdin-origin clause.
        self.assertFalse(result['source_audit_complete'])

    def test_controller_direct_dispatch_is_forbidden_at_its_actual_source_edge(self):
        source = self.SOURCE.replace('(void)player;', 'Dispatch(7);')
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(source)
        self.assertEqual(str(caught.exception), 'lcer.source_input_forbidden')
        self.assertEqual(caught.exception.edge['path'], str(self.path))
        self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceGameMode::RestartPlayer')
        self.assertEqual(caught.exception.edge['callee'], 'ACityLiveEvidenceGameMode::Dispatch')
        self.assertEqual(caught.exception.edge['input'], 'world')
        self.assertTrue(caught.exception.compiler_identity['callee_usr'])

    def test_controller_helper_path_into_virtual_tick_is_not_erased(self):
        source = self.SOURCE.replace('(void)player;', 'Helper();')
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(source)
        self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceGameMode::RestartPlayer')
        self.assertEqual(caught.exception.edge['input'], 'world')
        self.assertEqual([row['callee'] for row in caught.exception.call_path],
                         ['ACityLiveEvidenceGameMode::Helper', 'ACityLiveEvidenceGameMode::Tick'])

    def test_protected_method_pointer_cannot_be_captured_or_passed(self):
        for body in ('auto invoke = &ACityLiveEvidenceGameMode::Dispatch; (this->*invoke)(7);',
                     'auto invoke = [this] { Dispatch(7); }; invoke();',
                     'auto method = &ACityLiveEvidenceGameMode::EnqueueInput; (this->*method)(7);'):
            with self.subTest(body=body), self.assertRaises(self.verifier.SourceInputForbidden):
                self.check(self.SOURCE.replace('(void)player;', body))

    def test_helper_cannot_invoke_actor_or_insert_command(self):
        for body, callee in (('Resource.Interact(7);', 'ACityLiveEvidenceResource::Interact'),
                             ('EnqueueInput(7);', 'ACityLiveEvidenceGameMode::EnqueueInput')):
            with self.subTest(callee=callee), self.assertRaises(self.verifier.SourceInputForbidden) as caught:
                self.check(self.SOURCE.replace('void Helper() { Tick(0); }', 'void Helper() { ' + body + ' }'))
            self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceGameMode::Helper')
            self.assertEqual(caught.exception.edge['callee'], callee)

    def test_unknown_controller_callback_stays_unclassified(self):
        source = 'extern void external_controller_hook(void *);\n' + self.SOURCE.replace(
            '(void)player;', 'external_controller_hook(player);')
        result = self.check(source)
        self.assertEqual([row['callee'] for row in result['unclassified']], ['external_controller_hook'])
        self.assertFalse(result['source_audit_complete'])

    def test_ambiguous_role_overload_cannot_be_selected_by_name(self):
        source = self.SOURCE.replace('void Dispatch(int line)', 'void Dispatch(double) {}\n    void Dispatch(int line)')
        with self.assertRaisesRegex(ValueError, '^lcer.source_inventory_invalid$'):
            self.check(source)


class CppProbeReadClosureTests(unittest.TestCase):
    """Compiler-derived read paths only; fixture objects are not a world census."""

    SOURCE = '''
struct ACityLiveEvidenceActor {
    int RawSha256 = 0;
    int AcceptedRecordRaw = 0;
    int Read() const { return RawSha256; }
};
struct ACityLiveEvidenceGameMode;
extern ACityLiveEvidenceGameMode *Active;
int CollectWorlds(const ACityLiveEvidenceActor &actor);
struct ACityLiveEvidenceGameMode {
    int Domain = 0, Witness = 0, Launch = 0, BindingHash = 0;
    int PendingCommand = 0, ArmedFault = 0, CurrentRaw = 0;
    int Routing() const { return Domain + Witness + Launch + BindingHash; }
    int Helper() const { return 1; }
    int Observe(const ACityLiveEvidenceActor &actor) const {
        int rows = CollectWorlds(actor);
        return rows + Routing();
    }
};
int CollectWorlds(const ACityLiveEvidenceActor &actor) { return actor.Read(); }
'''

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier
        temporary = tempfile.TemporaryDirectory(prefix='city-probe-read-closure-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'probe.cpp'
        self.argv = ['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang',
                     '-x', 'c++', '-std=c++20', '-fsyntax-only']

    def check(self, source):
        self.path.write_text(source)
        inventory = self.verifier.ClangSourceInventory().parse(self.path, [str(self.path)], self.argv)
        self.assertEqual(inventory['diagnostics'], [])
        return self.verifier.CppProbeReadClosure([inventory], {str(self.path): self.path.read_bytes()}).check()

    def test_physical_slot_and_separate_routing_reads_keep_their_origins(self):
        result = self.check(self.SOURCE)
        pairs = {(row['callee'], row['input'], row['consequence']) for row in result['edges']}
        self.assertIn(('ACityLiveEvidenceActor::RawSha256', 'world', 'observation'), pairs)
        self.assertIn(('ACityLiveEvidenceGameMode::Domain', 'binding', 'provenance'), pairs)
        self.assertIn('probe_wrapper_routing_order_and_use_unresolved', {row['reason'] for row in result['unclassified']})
        self.assertFalse(result['source_audit_complete'])

    def test_expected_command_record_and_fault_selector_are_forbidden(self):
        for field, kind in [('PendingCommand', 'command'), ('CurrentRaw', 'canonical'), ('ArmedFault', 'command')]:
            with self.subTest(field=field), self.assertRaises(self.verifier.SourceInputForbidden) as caught:
                self.check(self.SOURCE.replace('return rows + Routing();', 'return rows + ' + field + ';'))
            self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceGameMode::Observe')
            self.assertEqual(caught.exception.edge['callee'], 'ACityLiveEvidenceGameMode::' + field)
            self.assertEqual(caught.exception.edge['input'], kind)
            self.assertTrue(caught.exception.compiler_identity['field_usr'])

    def test_helper_alias_and_lambda_do_not_hide_expected_record_reads(self):
        source = self.SOURCE.replace('int Helper() const { return 1; }',
                                    'int Helper() const { const int &renamed = CurrentRaw; return renamed; }')
        source = source.replace('return rows + Routing();', 'return rows + Helper();')
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(source)
        self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceGameMode::Helper')
        self.assertEqual(caught.exception.edge['input'], 'canonical')
        self.assertTrue(any(row['callee'] == 'ACityLiveEvidenceGameMode::Helper' for row in caught.exception.call_path))
        source = self.SOURCE.replace('return rows + Routing();',
                                    'auto select = [this] { return CurrentRaw; }; return rows + select();')
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(source)
        self.assertEqual(caught.exception.edge['callee'], 'ACityLiveEvidenceGameMode::CurrentRaw')

    def test_actor_record_cannot_replace_its_actual_observation_slot(self):
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(self.SOURCE.replace('return RawSha256;', 'return AcceptedRecordRaw;'))
        self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceActor::Read')
        self.assertEqual(caught.exception.edge['input'], 'canonical')

    def test_routing_is_not_a_permitted_input_to_the_probe(self):
        source = self.SOURCE.replace('{ return actor.Read(); }', '{ return actor.Read() + Active->Routing(); }')
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(source)
        self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceGameMode::Routing')
        self.assertEqual(caught.exception.edge['input'], 'binding')

    def test_shared_helper_is_checked_in_each_context(self):
        source = self.SOURCE.replace('int Helper() const { return 1; }', 'int Helper() const { return Domain; }')
        source = source.replace('return Domain + Witness + Launch + BindingHash;', 'return Helper();')
        result = self.check(source)
        self.assertIn(('ACityLiveEvidenceGameMode::Helper', 'routing'),
                      {(row['function'], row['context']) for row in result['visited']})
        with self.assertRaises(self.verifier.SourceInputForbidden):
            self.check(source.replace('return rows + Routing();', 'return rows + Routing() + Helper();'))

    def test_matching_field_name_in_other_class_is_not_the_same_storage(self):
        source = 'struct Other { int CurrentRaw = 0; };\n' + self.SOURCE.replace(
            'return rows + Routing();', 'Other unrelated; return rows + Routing() + unrelated.CurrentRaw;')
        result = self.check(source)
        self.assertTrue(any(row['field'] == 'Other::CurrentRaw' for row in result['field_reads']))
        self.assertIn('probe_field_receiver_origin_unresolved', {row['reason'] for row in result['unclassified']})


class CppSuccessfulCallGuardTests(unittest.TestCase):
    SOURCE = '''
struct Resource {
    bool Interact(int &result) { result = 7; return true; }
};
struct Mode {
    Resource resource;
    bool blocked = false;
    void Send(int result) {}
    void Dispatch() {
        int result = 0;
        if (blocked || !resource.Interact(result)) { return; }
        Send(result);
    }
};
'''

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier
        temporary = tempfile.TemporaryDirectory(prefix='city-successful-call-guard-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'guard.cpp'

    def check(self, source):
        self.path.write_text(source)
        argv = ['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang',
                '-x', 'c++', '-std=c++20', '-fsyntax-only']
        inventory = self.verifier.ClangSourceInventory().parse(self.path, [str(self.path)], argv)
        self.assertEqual(inventory['diagnostics'], [])
        return self.verifier.CppSuccessfulCallGuard([inventory], {str(self.path): self.path.read_bytes()}).check(
            'Mode::Dispatch', 'Resource::Interact', 'Mode::Send')

    def test_successful_actor_call_dominates_send(self):
        result = self.check(self.SOURCE)
        self.assertEqual(result['guards'][0]['sink_states'], ['required_call_returned_true'])
        self.assertFalse(result['source_audit_complete'])
        self.assertIn('sink_payload_origin_and_alias_writes', result['remaining_obligations'])

    def test_missing_actor_call_cannot_be_an_empty_positive(self):
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(self.SOURCE.replace('!resource.Interact(result)', 'false'))
        self.assertEqual(caught.exception.edge['path'], str(self.path))
        self.assertEqual(caught.exception.edge['function'], 'Mode::Dispatch')
        self.assertEqual(caught.exception.edge['input'], 'command')
        self.assertEqual(caught.exception.edge['callee'], 'Mode::Send')

    def test_short_circuit_bypass_and_inverted_result_reject(self):
        for source in (self.SOURCE.replace('blocked ||', 'blocked &&'),
                       self.SOURCE.replace('!resource.Interact', 'resource.Interact')):
            with self.subTest(source=source), self.assertRaises(self.verifier.SourceInputForbidden):
                self.check(source)

    def test_failure_path_must_return_on_every_branch(self):
        for body in ('', 'if (blocked) return;'):
            with self.subTest(body=body), self.assertRaises(self.verifier.SourceInputForbidden):
                self.check(self.SOURCE.replace('{ return; }', '{ ' + body + ' }'))

    def test_explicit_success_branch_and_double_negation_pass(self):
        source = self.SOURCE.replace('if (blocked || !resource.Interact(result)) { return; }\n        Send(result);',
                                    'if (!!resource.Interact(result)) Send(result); else return;')
        self.assertEqual(len(self.check(source)['guards']), 1)

    def test_send_before_guard_rejects(self):
        source = self.SOURCE.replace('if (blocked ||', 'Send(result);\n        if (blocked ||')
        with self.assertRaises(self.verifier.SourceInputForbidden):
            self.check(source)

    def test_jump_and_saved_boolean_remain_unclassified(self):
        for source in (self.SOURCE.replace('int result = 0;', 'int result = 0; goto after;').replace('Send(result);', 'after: Send(result);'),
                       self.SOURCE.replace('if (blocked || !resource.Interact(result))',
                                           'bool saved = resource.Interact(result); if (blocked || !saved)')):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, '^lcer.source_control_flow_unclassified$'):
                self.check(source)

    def test_separate_guarded_scopes_keep_distinct_call_results(self):
        source = self.SOURCE.replace('int result = 0;', 'int result = 0;\n        if (blocked) {\n')
        source = source.replace('Send(result);', 'Send(result);\n        } else {\n'
                                '            if (!resource.Interact(result)) return;\n            Send(result);\n        }')
        self.assertEqual(len(self.check(source)['guards']), 2)

    def test_boolean_sink_still_requires_guard_success(self):
        source = self.SOURCE.replace('void Send(int result) {}', 'bool Send(int result) { return result != 0; }')
        source = source.replace('Send(result);', 'if (blocked || !Send(result)) return;')
        self.assertEqual(len(self.check(source)['guards']), 1)
        with self.assertRaises(self.verifier.SourceInputForbidden):
            self.check(source.replace('{ return; }', '{}'))


class CppFaultStateWriterTests(unittest.TestCase):
    SOURCE = '''
struct ACityLiveEvidenceGameMode {
    int ArmedFault = 0;
    bool bFaultConsumed = false, other = false;
    void ArmFault() { ArmedFault = 7; }
    void ConsumeFault() { bFaultConsumed = true; }
    void Helper() {}
    void RestartPlayer() {}
};
'''

    def setUp(self):
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        self.verifier = verifier
        temporary = tempfile.TemporaryDirectory(prefix='city-fault-state-writers-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'writers.cpp'

    def check(self, source):
        self.path.write_text(source)
        argv = ['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang',
                '-x', 'c++', '-std=c++20', '-fsyntax-only']
        inventory = self.verifier.ClangSourceInventory().parse(self.path, [str(self.path)], argv)
        self.assertEqual(inventory['diagnostics'], [])
        return self.verifier.CppFaultStateWriters([inventory], {str(self.path): self.path.read_bytes()}).check()

    def test_two_declared_owners_keep_native_field_identities(self):
        result = self.check(self.SOURCE)
        self.assertEqual({r['function'].split('::')[-1] for r in result['writes']}, {'ArmFault', 'ConsumeFault'})
        self.assertEqual(len(result['writes']), 2)
        self.assertTrue(all(r['field_usr'] and r['caller_usr'] for r in result['writes']))
        self.assertFalse(result['all_field_writers_classified'])
        self.assertFalse(result['stage_semantics_accepted'])
        self.assertFalse(result['source_audit_complete'])

    def test_controller_and_helper_direct_writes_reject_at_actual_statement(self):
        for method, kind in [('Helper', 'command'), ('RestartPlayer', 'world')]:
            source = self.SOURCE.replace('void '+method+'() {}', 'void '+method+'() { bFaultConsumed = true; }')
            with self.subTest(method=method), self.assertRaises(self.verifier.SourceInputForbidden) as caught:
                self.check(source)
            self.assertEqual(str(caught.exception), 'lcer.source_input_forbidden')
            self.assertEqual(caught.exception.edge['path'], str(self.path))
            self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceGameMode::'+method)
            self.assertEqual(caught.exception.edge['callee'], 'ACityLiveEvidenceGameMode::bFaultConsumed')
            self.assertEqual(caught.exception.edge['input'], kind)

    def test_local_reference_alias_does_not_hide_unauthorized_write(self):
        with self.assertRaises(self.verifier.SourceInputForbidden):
            self.check(self.SOURCE.replace('void Helper() {}',
                'void Helper() { bool &alias = bFaultConsumed; alias = true; }'))

    def test_pointer_assignment_and_alias_chain_keep_possible_field_target(self):
        for body in ('bool *p = nullptr; p = &bFaultConsumed; *p = true;',
                     'bool *p = &bFaultConsumed; auto *q = p; *q = true;',
                     'bool *p = &bFaultConsumed; p = &other; *p = true;'):
            with self.subTest(body=body), self.assertRaises(self.verifier.SourceInputForbidden):
                self.check(self.SOURCE.replace('void Helper() {}', 'void Helper() { '+body+' }'))

    def test_pointer_to_member_cannot_bypass_field_owner(self):
        with self.assertRaises(self.verifier.SourceInputForbidden):
            self.check(self.SOURCE.replace('void Helper() {}',
                'void Helper() { auto member = &ACityLiveEvidenceGameMode::bFaultConsumed; this->*member = true; }'))

    def test_copy_is_distinct_and_other_class_same_spelling_is_distinct(self):
        source = 'struct Other { bool bFaultConsumed = false; };\n' + self.SOURCE
        source = source.replace('void Helper() {}',
            'void Helper() { bool copy = bFaultConsumed; copy = true; Other x; x.bFaultConsumed = true; }')
        self.assertEqual(len(self.check(source)['writes']), 2)

    def test_alias_writes_inside_owner_retain_alias_proof_obligation(self):
        source = self.SOURCE.replace('bFaultConsumed = true;', 'bool &alias = bFaultConsumed; alias = true;')
        result = self.check(source)
        self.assertEqual(len(result['writes']), 2)
        self.assertTrue(result['reference_aliases'])
        self.assertIn('fault_reference_alias_effects_unresolved', {r['reason'] for r in result['unclassified']})

    def test_overloaded_handle_assignment_and_mutable_receiver_are_checked(self):
        source = 'struct Handle { Handle& operator=(int) { return *this; } void Reset() {} bool IsValid() const { return true; } };\n'
        source += self.SOURCE.replace('int ArmedFault = 0;', 'Handle ArmedFault;')
        result = self.check(source)
        self.assertIn('possible_native_receiver_write', {r['operation'] for r in result['writes']})
        with self.assertRaises(self.verifier.SourceInputForbidden):
            self.check(source.replace('void Helper() {}', 'void Helper() { ArmedFault.Reset(); }'))
        readonly = self.check(source.replace('void Helper() {}', 'void Helper() { ArmedFault.IsValid(); }'))
        self.assertIn('native_fault_handle_method_effects_unresolved', {r['reason'] for r in readonly['unclassified']})

    def test_pointer_escape_and_reference_argument_are_not_marked_complete(self):
        source = 'extern void take(bool*); extern void mutate(bool&);\n' + self.SOURCE
        source = source.replace('void Helper() {}', 'void Helper() { take(&bFaultConsumed); mutate(bFaultConsumed); }')
        result = self.check(source)
        reasons = {r['reason'] for r in result['unclassified']}
        self.assertIn('fault_storage_pointer_escape_unresolved', reasons)
        self.assertIn('fault_storage_argument_effects_unresolved', reasons)
        self.assertFalse(result['all_field_writers_classified'])

    def test_helper_reference_parameter_keeps_fault_storage_identity(self):
        source = self.SOURCE.replace('void Helper() {}', 'void Helper(bool &value) { value = true; }')
        source = source.replace('void RestartPlayer() {}', 'void RestartPlayer() { Helper(bFaultConsumed); }')
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(source)
        self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceGameMode::Helper')
        self.assertEqual(caught.exception.edge['callee'], 'ACityLiveEvidenceGameMode::bFaultConsumed')

    def test_pointer_parameter_chain_uses_definition_parameters_not_forward_names(self):
        source = 'void Write(bool *prototype_name); void Relay(bool *x) { Write(x); }\n' + self.SOURCE
        source = source.replace('void RestartPlayer() {}', 'void RestartPlayer() { Relay(&bFaultConsumed); }')
        source += '\nvoid Write(bool *actual_name) { *actual_name = true; }\n'
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(source)
        self.assertEqual(caught.exception.edge['function'], 'Write')
        self.assertEqual(caught.exception.edge['callee'], 'ACityLiveEvidenceGameMode::bFaultConsumed')

    def test_helper_pointer_and_reference_returns_reach_call_site_writes(self):
        for method, expression in [('bool *Alias() { return &bFaultConsumed; }', '*Alias() = true;'),
                                   ('bool &Alias() { return bFaultConsumed; }', 'Alias() = true;')]:
            source = self.SOURCE.replace('void Helper() {}', method)
            source = source.replace('void RestartPlayer() {}', 'void RestartPlayer() { '+expression+' }')
            with self.subTest(method=method), self.assertRaises(self.verifier.SourceInputForbidden) as caught:
                self.check(source)
            self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceGameMode::RestartPlayer')
            self.assertEqual(caught.exception.edge['input'], 'world')

    def test_reference_forwarding_connects_actual_formal_and_return(self):
        source = 'bool &Identity(bool &value) { return value; }\n' + self.SOURCE
        source = source.replace('void RestartPlayer() {}', 'void RestartPlayer() { Identity(bFaultConsumed) = true; }')
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(source)
        self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceGameMode::RestartPlayer')

    def test_recursive_return_alias_converges_without_losing_field(self):
        source = 'bool &Follow(bool &value, int depth) { if (depth > 0) return Follow(value, depth - 1); return value; }\n' + self.SOURCE
        source = source.replace('void RestartPlayer() {}', 'void RestartPlayer() { Follow(bFaultConsumed, 2) = true; }')
        with self.assertRaises(self.verifier.SourceInputForbidden):
            self.check(source)

    def test_value_return_does_not_turn_copied_boolean_into_fault_storage(self):
        source = self.SOURCE.replace('void Helper() {}', 'bool Copy() { return bFaultConsumed; }')
        source = source.replace('void RestartPlayer() {}', 'void RestartPlayer() { bool copy = Copy(); copy = true; }')
        result = self.check(source)
        self.assertEqual(len(result['writes']), 2)
        self.assertEqual(result['returned_aliases'], [])

    def test_overloads_bind_only_the_compiler_selected_parameter(self):
        source = 'void Visit(bool value) { value = true; } void Visit(int *p) { *p = 4; }\n' + self.SOURCE
        source = source.replace('void RestartPlayer() {}', 'void RestartPlayer() { Visit(bFaultConsumed); }')
        result = self.check(source)
        self.assertEqual(result['call_aliases'], [])
        self.assertEqual(len(result['writes']), 2)

    def test_function_object_receiver_does_not_shift_explicit_reference_argument(self):
        source = 'struct Writer { void operator()(bool &value) { value = true; } };\n' + self.SOURCE
        source = source.replace('void RestartPlayer() {}', 'void RestartPlayer() { Writer writer; writer(bFaultConsumed); }')
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(source)
        self.assertEqual(caught.exception.edge['function'], 'Writer::operator()')

    def test_owner_using_returned_alias_retains_call_context_and_lifetime_obligations(self):
        source = 'bool &Identity(bool &value) { return value; }\n' + self.SOURCE
        source = source.replace('void ConsumeFault() { bFaultConsumed = true; }',
                                'void ConsumeFault() { Identity(bFaultConsumed) = true; }')
        result = self.check(source)
        self.assertEqual(len(result['writes']), 2)
        self.assertTrue(result['call_aliases'])
        self.assertTrue(result['returned_aliases'])
        self.assertTrue(all(row['parameter_usr'] and row['callee_usr'] for row in result['call_aliases']))
        self.assertEqual({r['result_type_kind'] for r in result['returned_aliases']}, {'LValueReference'})
        reasons = {r['reason'] for r in result['unclassified']}
        self.assertIn('fault_formal_alias_context_and_lifetime_unresolved', reasons)
        self.assertIn('fault_return_alias_context_and_lifetime_unresolved', reasons)
        self.assertFalse(result['all_field_writers_classified'])

    def test_missing_native_return_type_cannot_hide_a_returned_alias(self):
        source = self.SOURCE.replace('void Helper() {}', 'bool &Alias() { return bFaultConsumed; }')
        self.path.write_text(source)
        argv = ['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang',
                '-x', 'c++', '-std=c++20', '-fsyntax-only']
        inventory = self.verifier.ClangSourceInventory().parse(self.path, [str(self.path)], argv)
        alias = next(n for n in inventory['nodes'] if n['kind'] == 'CXXMethod' and n['definition']
                     and n['qualified'] == 'ACityLiveEvidenceGameMode::Alias')
        self.assertEqual(alias['result_type_kind'], 'LValueReference')
        del alias['result_type_kind']
        with self.assertRaisesRegex(ValueError, '^lcer.source_inventory_invalid$'):
            self.verifier.CppFaultStateWriters([inventory], {str(self.path): self.path.read_bytes()}).check()


class CppFaultReadinessPredicateTests(unittest.TestCase):
    SOURCE = '#define TEXT(x) u##x\nstruct FString { FString(); FString(const char16_t*); };\nstruct TStringView { TStringView(const char16_t*); };\nstruct FJsonObject { bool TryGetStringField(TStringView, FString&) const; };\ntemplate<class T> struct TSharedPtr { bool IsValid() const; T* operator->() const; };\nnamespace CityLCER { bool Exact(const FString&, const FString&); }\nstruct ACityLiveEvidenceGameMode {\n bool bTerminal, bFaultConsumed, bBound, bEmitted;\n int CurrentGeneration, PendingGeneration;\n TSharedPtr<FJsonObject> ArmedFault, PendingCommand;\n FString Witness, Domain;\n bool FaultReady(const FString& Stage) const;\n};\nbool ACityLiveEvidenceGameMode::FaultReady(const FString& Stage) const\n{\n    if (bTerminal || bFaultConsumed || !bBound || !bEmitted || CurrentGeneration != 1 || PendingGeneration != 1 ||\n        !ArmedFault.IsValid() || !PendingCommand.IsValid()) return false;\n    FString Case;\n    FString ArmedStage;\n    FString ArmedOperation;\n    FString PendingOperation;\n    if (!ArmedFault->TryGetStringField(TEXT("failure_case"), Case) ||\n        !ArmedFault->TryGetStringField(TEXT("stage"), ArmedStage) ||\n        !ArmedFault->TryGetStringField(TEXT("operation_id"), ArmedOperation) ||\n        !PendingCommand->TryGetStringField(TEXT("operation_id"), PendingOperation)) return false;\n    if (!CityLCER::Exact(Case, Witness) || !CityLCER::Exact(ArmedStage, Stage) ||\n        !CityLCER::Exact(ArmedOperation, TEXT("materialize_0002")) ||\n        !CityLCER::Exact(PendingOperation, ArmedOperation)) return false;\n    const bool bPartial = CityLCER::Exact(Case, TEXT("F13")) || CityLCER::Exact(Case, TEXT("F14"));\n    const bool bAfterReceipt = CityLCER::Exact(Case, TEXT("F15")) || CityLCER::Exact(Case, TEXT("F16a")) || CityLCER::Exact(Case, TEXT("F16b"));\n    return (bPartial || bAfterReceipt) &&\n        CityLCER::Exact(Domain, CityLCER::Exact(Case, TEXT("F14")) ? TEXT("domain_B") : TEXT("domain_A")) &&\n        CityLCER::Exact(Stage, bPartial ? TEXT("after_resource_before_anchor") : TEXT("after_receipt_before_observation"));\n}\n\n'

    def setUp(self):
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        self.verifier = verifier
        temporary = tempfile.TemporaryDirectory(prefix='city-readiness-predicate-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'readiness.cpp'

    def check(self, source):
        self.path.write_text(source)
        argv = ['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang',
                '-x', 'c++', '-std=c++20', '-fsyntax-only']
        inventory = self.verifier.ClangSourceInventory().parse(self.path, [str(self.path)], argv)
        self.assertEqual(inventory['diagnostics'], [])
        return self.verifier.CppFaultReadinessPredicate([inventory], {str(self.path): self.path.read_bytes()}).check()

    def rejected(self, source):
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(source)
        self.assertEqual(str(caught.exception), 'lcer.source_input_forbidden')
        self.assertEqual(caught.exception.edge['path'], str(self.path))
        self.assertEqual(caught.exception.edge['function'], 'ACityLiveEvidenceGameMode::FaultReady')
        self.assertEqual(caught.exception.edge['input'], 'command')

    def test_full_success_relation_has_exact_five_frozen_rows(self):
        result = self.check(self.SOURCE)
        self.assertEqual(len(result['normalized_success_rows']), 5)
        self.assertEqual(len(result['json_bindings']), 4)
        self.assertEqual(len(result['guard_nodes']), 3)
        self.assertTrue(result['logical_relation_matches_frozen_hooks'])
        self.assertFalse(result['native_effects_accepted'])
        self.assertFalse(result['field_lifetime_accepted'])
        self.assertFalse(result['all_stage_semantics_accepted'])
        self.assertFalse(result['source_audit_complete'])

    def test_lifecycle_and_handle_guards_cannot_be_dropped_or_inverted(self):
        for term in ('bTerminal', 'bFaultConsumed', '!bBound', '!bEmitted', '!ArmedFault.IsValid()', '!PendingCommand.IsValid()'):
            with self.subTest(term=term):
                self.rejected(self.SOURCE.replace(term+' ||', 'false ||', 1) if term+' ||' in self.SOURCE
                              else self.SOURCE.replace(term+') return false;', 'false) return false;', 1))
        self.rejected(self.SOURCE.replace('!bBound ||', 'bBound ||'))

    def test_both_generation_equalities_are_required(self):
        for name in ('CurrentGeneration', 'PendingGeneration'):
            with self.subTest(name=name):
                self.rejected(self.SOURCE.replace(name+' != 1', name+' != 2'))
                self.rejected(self.SOURCE.replace(name+' != 1', 'false'))

    def test_json_outputs_are_bound_to_the_actual_object_and_key(self):
        self.rejected(self.SOURCE.replace('TEXT("failure_case"), Case', 'TEXT("stage"), Case'))
        self.rejected(self.SOURCE.replace('ArmedFault->TryGetStringField(TEXT("operation_id")',
                                         'PendingCommand->TryGetStringField(TEXT("operation_id")'))
        self.rejected(self.SOURCE.replace('TEXT("failure_case"), Case', 'TEXT("failure_case"), ArmedStage'))

    def test_witness_and_operation_binding_cannot_be_weakened(self):
        self.rejected(self.SOURCE.replace('CityLCER::Exact(Case, Witness)', 'CityLCER::Exact(Case, Case)'))
        self.rejected(self.SOURCE.replace('CityLCER::Exact(PendingOperation, ArmedOperation)',
                                         'CityLCER::Exact(ArmedOperation, ArmedOperation)'))
        self.rejected(self.SOURCE.replace('TEXT("materialize_0002")', 'TEXT("materialize_0001")'))

    def test_hook_membership_domain_and_stage_are_exact(self):
        for old, new in [('TEXT("F16b")', 'TEXT("F16")'), ('TEXT("domain_B")', 'TEXT("domain_A")'),
                         ('TEXT("after_resource_before_anchor")', 'TEXT("after_receipt_before_observation")')]:
            with self.subTest(old=old):
                self.rejected(self.SOURCE.replace(old, new))

    def test_native_json_read_cannot_precede_its_handle_validity_guard(self):
        start = self.SOURCE.index('    if (bTerminal')
        end = self.SOURCE.index('    FString Case;', start)
        guard = self.SOURCE[start:end]
        moved = self.SOURCE[:start] + self.SOURCE[end:]
        moved = moved.replace('    if (!CityLCER::Exact(Case, Witness)', guard+'    if (!CityLCER::Exact(Case, Witness)')
        self.rejected(moved)

    def test_unmodeled_early_success_is_not_accepted(self):
        self.rejected(self.SOURCE.replace('    if (bTerminal', '    if (bBound) return true;\n    if (bTerminal'))

    def test_logically_equivalent_guard_order_preserves_the_relation(self):
        changed = self.SOURCE.replace('bTerminal || bFaultConsumed', 'bFaultConsumed || bTerminal')
        changed = changed.replace('CurrentGeneration != 1', '!(CurrentGeneration == 1)')
        self.assertEqual(len(self.check(changed)['normalized_success_rows']), 5)


class CppFieldWriteGuardTests(unittest.TestCase):
    SOURCE = '''
struct Mode {
    bool consumed = false, blocked = false;
    bool Ready() const { return !blocked; }
    void Consume() {
        if (!Ready()) return;
        consumed = true;
    }
};
'''

    def setUp(self):
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        self.verifier = verifier
        temporary = tempfile.TemporaryDirectory(prefix='city-field-write-guard-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'field.cpp'

    def check(self, source):
        self.path.write_text(source)
        argv = ['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang',
                '-x', 'c++', '-std=c++20', '-fsyntax-only']
        inventory = self.verifier.ClangSourceInventory().parse(self.path, [str(self.path)], argv)
        self.assertEqual(inventory['diagnostics'], [])
        self.assertEqual(inventory['visitor_errors'], [])
        return self.verifier.CppSuccessfulCallGuard([inventory], {str(self.path): self.path.read_bytes()}).check_field_write(
            'Mode::Consume', 'Mode::Ready', 'Mode::consumed'), inventory

    def test_native_assignment_requires_successful_ready_call(self):
        result, inventory = self.check(self.SOURCE)
        self.assertEqual(len(result['guards']), 1)
        proof = result['guards'][0]
        self.assertEqual(proof['sink_states'], ['required_call_returned_true'])
        assignment = inventory['nodes'][proof['sink_node'][1]]
        self.assertEqual((assignment['kind'], assignment['binary_operator']), ('BinaryOperator', '='))
        self.assertEqual(result['sink_kind'], 'direct_builtin_field_assignment')
        self.assertFalse(result['all_field_writers_classified'])
        self.assertFalse(result['receiver_identity_accepted'])
        self.assertFalse(result['source_audit_complete'])

    def test_missing_ready_reports_actual_field_edge(self):
        with self.assertRaises(self.verifier.SourceInputForbidden) as caught:
            self.check(self.SOURCE.replace('if (!Ready()) return;', ''))
        self.assertEqual(str(caught.exception), 'lcer.source_input_forbidden')
        edge = caught.exception.edge
        self.assertEqual(edge['path'], str(self.path))
        self.assertEqual((edge['function'], edge['callee'], edge['input']),
                         ('Mode::Consume', 'Mode::consumed', 'command'))
        self.assertGreater(edge['line'], 0)
        self.assertTrue(caught.exception.compiler_identity['sink_usr'])

    def test_inverted_fallthrough_and_short_circuit_bypasses_reject(self):
        for guard in ('if (Ready()) return;', 'if (!Ready()) {}',
                      'if (blocked && !Ready()) return;'):
            with self.subTest(guard=guard), self.assertRaises(self.verifier.SourceInputForbidden):
                self.check(self.SOURCE.replace('if (!Ready()) return;', guard))

    def test_write_before_readiness_rejects_even_with_guarded_later_write(self):
        source = self.SOURCE.replace('if (!Ready()) return;', 'consumed = true; if (!Ready()) return;')
        with self.assertRaises(self.verifier.SourceInputForbidden):
            self.check(source)

    def test_read_on_right_side_does_not_count_as_field_write(self):
        with self.assertRaisesRegex(ValueError, '^lcer.source_field_write_unclassified$'):
            self.check(self.SOURCE.replace('consumed = true;', 'blocked = consumed;'))

    def test_other_class_same_spelling_does_not_supply_or_invalidate_target_write(self):
        source = 'struct Other { bool consumed = false; };\n' + self.SOURCE
        source = source.replace('if (!Ready()) return;', 'Other other; other.consumed = true; if (!Ready()) return;')
        result, _ = self.check(source)
        self.assertEqual(len(result['guards']), 1)
        with self.assertRaisesRegex(ValueError, '^lcer.source_field_write_unclassified$'):
            self.check(source.replace('        consumed = true;', ''))

    def test_aliased_and_compound_writes_do_not_get_empty_direct_write_proof(self):
        for write in ('bool &alias = consumed; alias = true;', 'consumed |= true;'):
            with self.subTest(write=write), self.assertRaisesRegex(ValueError, '^lcer.source_field_write_unclassified$'):
                self.check(self.SOURCE.replace('consumed = true;', write))

    def test_parenthesized_field_and_explicit_success_branch_are_checked(self):
        source = self.SOURCE.replace('if (!Ready()) return;\n        consumed = true;',
                                    'if (!!Ready()) (this->consumed) = true; else return;')
        result, _ = self.check(source)
        self.assertEqual(len(result['guards']), 1)

    def test_direct_proof_retains_alias_and_stage_semantic_obligations(self):
        source = self.SOURCE.replace('if (!Ready()) return;',
                                    'bool &alias = consumed; alias = true; if (!Ready()) return;')
        result, _ = self.check(source)
        self.assertFalse(result['all_field_writers_classified'])
        self.assertIn('field_alias_and_overloaded_assignment_writers', result['remaining_obligations'])
        self.assertIn('required_call_stage_semantics', result['remaining_obligations'])


class NativeSharedCacheTests(unittest.TestCase):
    """Independent cache decoding over ordinary disposable files."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier
        self.policy = json.loads(CONTRACT_PATH.read_bytes())
        temporary = tempfile.TemporaryDirectory(prefix='city-independent-cache-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.main = ProcessByteParserTests()._cache_fixture(self.directory)
        self.sub = Path(str(self.main) + '.01')
        self.original = {self.main: self.main.read_bytes(), self.sub: self.sub.read_bytes()}

    def restore(self):
        for path, raw in self.original.items():
            path.write_bytes(raw)

    def records(self):
        return [{'realpath': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'size_bytes': path.stat().st_size}
                for path in (self.main, self.sub)]

    def decode(self):
        records = self.records()
        return self.verifier.native_shared_cache_inventory(self.verifier.ExternalFileSnapshot(records), records[0])

    def test_main_subcache_and_embedded_image_are_bound_to_actual_bytes(self):
        result = self.decode()
        self.assertEqual(result['files'], self.records())
        self.assertEqual(result['cache_uuids'], ['01020304-0506-0708-090a-0b0c0d0e0f10', '11121314-1516-1718-191a-1b1c1d1e1f20'])
        self.assertEqual(result['images'], [{'realpath': '/usr/lib/libfixture.dylib', 'sha256': self.records()[0]['sha256'],
            'macho_uuid': '21222324-2526-2728-292a-2b2c2d2e2f30', 'architecture': 'arm64e', 'source': 'dyld_shared_cache'}])
        self.assertEqual(len(result['mappings']), 2)
        self.assertEqual({key: result[key] for key in ('main', 'files', 'cache_uuids', 'images')}, dyld_cache_inventory(self.main))

    def test_hash_binding_and_missing_subcache_reject_before_acceptance(self):
        rows = self.records()
        files = self.verifier.ExternalFileSnapshot(rows)
        self.sub.write_bytes(self.sub.read_bytes()[:-1] + b'X')
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
            self.verifier.native_shared_cache_inventory(files, rows[0])
        self.restore()
        with self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_invalid$'):
            self.verifier.native_shared_cache_inventory(self.verifier.ExternalFileSnapshot(rows[:1]), rows[0])

    def test_rehashed_cache_header_and_mapping_attacks_reject(self):
        attacks = [(0, b'invalid'), (88, bytes(16)), (16, struct.pack('<II', 463, 1)), (20, struct.pack('<I', 0)),
                   (20, struct.pack('<I', 65)), (16, struct.pack('<I', 8190)), (512, struct.pack('<Q', 0)),
                   (520, struct.pack('<Q', 0)), (520, struct.pack('<Q', 10000)), (536, struct.pack('<I', 8)),
                   (540, struct.pack('<I', 7)), (540, struct.pack('<I', 1)), (396, struct.pack('<I', 65)),
                   (448, struct.pack('<II', 1024, 2)), (144, struct.pack('<Q', 100001)),
                   (136, struct.pack('<Q', 8180)), (1056, bytes(16)), (1072, struct.pack('<Q', 0xfffffffffffffff0)),
                   (1080, struct.pack('<I', 16)), (1080, struct.pack('<I', 8192)), (1052, struct.pack('<I', 1))]
        for offset, value in attacks:
            self.restore()
            raw = bytearray(self.main.read_bytes()); raw[offset:offset + len(value)] = value; self.main.write_bytes(raw)
            with self.subTest(offset=offset, value=value), self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_invalid$'):
                self.decode()

    def test_subcache_uuid_family_base_nested_entries_and_suffix_attacks_reject(self):
        attacks = [(self.sub, 88, b'X'), (self.sub, 0, b'dyld_v1  x86_64\0'),
                   (self.sub, 512, struct.pack('<Q', 0x100000001)), (self.sub, 396, struct.pack('<I', 1)),
                   (self.main, 1104, struct.pack('<Q', 1)), (self.main, 1112, b'../x\0'.ljust(32, b'\0')),
                   (self.main, 1112, b'.01\0bad'.ljust(32, b'\0')), (self.main, 1112, b'.01' + b'a' * 29)]
        for path, offset, value in attacks:
            self.restore()
            raw = bytearray(path.read_bytes()); raw[offset:offset + len(value)] = value; path.write_bytes(raw)
            with self.subTest(path=str(path), offset=offset), self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_invalid$'):
                self.decode()
        self.restore()
        raw = bytearray(self.main.read_bytes())
        raw[1536:1648] = raw[1088:1144] * 2
        struct.pack_into('<II', raw, 392, 1536, 2)
        self.main.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_invalid$'):
            self.decode()

    def test_image_indexes_and_embedded_macho_must_agree_after_rehash(self):
        attacks = [(1024, struct.pack('<Q', 0x100001001)), (1084, struct.pack('<I', 8192)),
                   (1144, b'relative\0'), (1144, b'\xff\0'), (4096, b'bad!'), (4100, struct.pack('<I', 0x01000007)),
                   (4108, struct.pack('<I', 1)), (4112, struct.pack('<I', 2)), (4116, struct.pack('<I', 300)),
                   (4124, struct.pack('<I', 1)), (4128, struct.pack('<I', 0x26)), (4132, struct.pack('<I', 8)), (4136, b'X')]
        for offset, value in attacks:
            self.restore()
            raw = bytearray(self.main.read_bytes()); raw[offset:offset + len(value)] = value; self.main.write_bytes(raw)
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_invalid$'):
                self.decode()

    def test_replicated_subcache_index_must_be_exact(self):
        raw = bytearray(self.sub.read_bytes()); first = self.main.read_bytes()
        for start, end in ((136, 152), (448, 456), (1024, 1088), (1144, 1200)):
            raw[start:end] = first[start:end]
        self.sub.write_bytes(raw)
        self.assertEqual(len(self.decode()['images']), 1)
        raw[1056] ^= 1; self.sub.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_invalid$'):
            self.decode()

    def test_embedded_image_can_reside_in_the_declared_subcache_mapping(self):
        first, second = bytearray(self.main.read_bytes()), bytearray(self.sub.read_bytes())
        second[1024:1080] = first[4096:4152]
        address = 0x100000000 + 8192 + 1024
        struct.pack_into('<Q', first, 1024, address)
        struct.pack_into('<Q', first, 1072, address)
        self.main.write_bytes(first); self.sub.write_bytes(second)
        self.assertEqual(self.decode()['images'][0]['architecture'], 'arm64e')
        second[1064] ^= 1; self.sub.write_bytes(second)
        with self.assertRaisesRegex(ValueError, '^lcer.dyld_cache_invalid$'):
            self.decode()

    def test_build_join_requires_cache_file_coverage_and_exact_loaded_rows(self):
        rows = self.records(); files = self.verifier.ExternalFileSnapshot(rows)
        inventory = self.verifier.native_shared_cache_inventory(files, rows[0])
        build = schema_example(self.policy['wire_schemas']['build_record'], self.policy['wire_schemas'])
        build['external_inputs'].update(dyld_cache=rows[0], build_inputs=rows, loaded_images=copy.deepcopy(inventory['images']))
        image_result = {'verified_file_images': [], 'unverified_cache_images': copy.deepcopy(inventory['images'])}
        result = self.verifier._build_cache_relations(self.policy, stored_json_bytes(build), files, image_result)
        self.assertEqual(result['verified_cache_images'], inventory['images'])
        self.assertEqual(result['available_cache_images'], 1)
        for defect in ('missing_file', 'missing_cached', 'invented_path', 'hash', 'uuid', 'architecture', 'source', 'duplicate'):
            changed = copy.deepcopy(build); component = copy.deepcopy(image_result)
            loaded = changed['external_inputs']['loaded_images']
            if defect == 'missing_file': changed['external_inputs']['build_inputs'].pop()
            elif defect == 'missing_cached': loaded.clear(); component['unverified_cache_images'].clear()
            elif defect == 'duplicate': loaded.append(dict(loaded[0]))
            else:
                field, value = {'invented_path': ('realpath', '/usr/lib/not-in-cache.dylib'), 'hash': ('sha256', 'f' * 64),
                                'uuid': ('macho_uuid', 'f' * 36), 'architecture': ('architecture', 'x86_64'), 'source': ('source', 'dyld')}[defect]
                loaded[0][field] = value
                component['unverified_cache_images'] = copy.deepcopy(loaded)
                if defect == 'source':
                    component['verified_file_images'] = [dict(loaded[0], file_type=6)]
                    component['unverified_cache_images'] = []
            with self.subTest(defect=defect), self.assertRaisesRegex(ValueError, '^lcer.(dyld_cache_invalid|image_identity_invalid)$'):
                self.verifier._build_cache_relations(self.policy, stored_json_bytes(changed), files, component)


class NativeFileImageIdentityTests(unittest.TestCase):
    """Small Mach-O identity tables and real disk reads, never loaded code."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier
        self.policy = json.loads(CONTRACT_PATH.read_bytes())
        temporary = tempfile.TemporaryDirectory(prefix='city-file-images-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.uuid = '00010203-0405-0607-0809-0a0b0c0d0e0f'

    def thin(self, cpu=0x0100000c, subtype=0, file_type=6):
        return struct.pack('<IiiIIIII', 0xfeedfacf, cpu, subtype, file_type, 1, 24, 0, 0) + struct.pack('<II', 0x1b, 24) + bytes(range(16))

    def fat(self, slices, wide=False):
        width = 32 if wide else 20
        offset = (8 + len(slices) * width + 63) & ~63
        entries = []; body = bytearray(offset)
        for raw in slices:
            cpu, subtype = struct.unpack_from('<ii', raw, 4)
            values = (cpu, subtype, offset, len(raw), 6)
            entries.append(struct.pack('>iiQQII', *values, 0) if wide else struct.pack('>iiIII', *values))
            body.extend(raw)
            body.extend(b'\0' * (-len(body) % 64))
            offset = len(body)
        header = (b'\xca\xfe\xba\xbf' if wide else b'\xca\xfe\xba\xbe') + struct.pack('>I', len(slices)) + b''.join(entries)
        body[:len(header)] = header
        return bytes(body)

    def identity(self, raw, path='/private/tmp/offline-native-image', architecture='arm64'):
        return {'realpath': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'macho_uuid': self.uuid,
                'architecture': architecture, 'source': 'dyld'}

    def test_thin_loadable_header_identities_are_derived_from_bytes(self):
        for cpu, subtype, architecture in ((0x0100000c, 0, 'arm64'), (0x0100000c, 2, 'arm64e'), (0x01000007, 3, 'x86_64')):
            for file_type in (2, 6, 7, 8):
                raw = self.thin(cpu, subtype, file_type)
                self.assertEqual(self.verifier.native_file_image_headers(raw), [{'architecture': architecture,
                    'macho_uuid': self.uuid, 'file_type': file_type, 'offset': 0, 'size_bytes': len(raw)}])

    def test_universal_32_and_64_bit_tables_select_one_compatible_family(self):
        for wide in (False, True):
            raw = self.fat([self.thin(0x01000007, 3, 2), self.thin(file_type=2)], wide)
            image = self.verifier.native_file_image_identity(raw, self.identity(raw))
            self.assertEqual(image, dict(self.identity(raw), file_type=2))
        for raw in (self.thin(0x01000007, 3), self.fat([self.thin(), self.thin(subtype=2)]), self.fat([self.thin(), self.thin()])):
            with self.assertRaisesRegex(ValueError, '^lcer.image_identity_invalid$'):
                self.verifier.native_file_image_identity(raw, self.identity(raw))

    def test_recorded_hash_uuid_architecture_and_source_cannot_override_raw_identity(self):
        raw = self.thin()
        for change in ({'sha256': 'f' * 64}, {'macho_uuid': 'f' * 36}, {'architecture': 'arm64e'},
                       {'architecture': 'x86_64'}, {'source': 'dyld_shared_cache'}, {'extra': True}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^lcer.image_identity_invalid$'):
                self.verifier.native_file_image_identity(raw, dict(self.identity(raw), **change))

    def test_malformed_load_commands_and_nonloadable_headers_reject_even_after_rehash(self):
        original = self.thin()
        attacks = [b'', original[:31], original[:-1], original[:32] + struct.pack('<II', 0x1b, 24)]
        for offset, value in ((0, 0), (4, 0), (8, 3), (12, 1), (16, 0), (16, 2),
                              (20, 25), (20, 100), (28, 1), (32, 0x26), (36, 0), (36, 8), (36, 23), (36, 32)):
            raw = bytearray(original); struct.pack_into('<I', raw, offset, value); attacks.append(bytes(raw))
        duplicate = bytearray(original + original[32:])
        struct.pack_into('<II', duplicate, 16, 2, 48)
        attacks.append(bytes(duplicate))
        for number, raw in enumerate(attacks):
            with self.subTest(attack=number), self.assertRaisesRegex(ValueError, '^lcer.image_identity_invalid$'):
                self.verifier.native_file_image_identity(raw, self.identity(raw))

    def test_fat_offsets_overlap_alignment_cpu_identity_and_reserved_fields_reject(self):
        original = self.fat([self.thin(0x01000007, 3), self.thin()])
        attacks = [original[:7], original[:25]]
        for offset, value in ((4, 0), (4, 33), (8, 0x0100000c), (16, 0), (16, 65), (20, 10000), (24, 32), (36, 64)):
            raw = bytearray(original); struct.pack_into('>I', raw, offset, value); attacks.append(bytes(raw))
        raw = bytearray(self.fat([self.thin()], wide=True)); struct.pack_into('>I', raw, 36, 1); attacks.append(bytes(raw))
        for number, raw in enumerate(attacks):
            with self.subTest(attack=number), self.assertRaisesRegex(ValueError, '^lcer.image_identity_invalid$'):
                self.verifier.native_file_image_identity(raw, self.identity(raw))

    def build(self, editor_type=2, editor_subtype=0, module_type=6, module_subtype=0):
        build = schema_example(self.policy['wire_schemas']['build_record'], self.policy['wire_schemas'])
        images = []
        for name, file_type, subtype in (('editor', editor_type, editor_subtype), ('module', module_type, module_subtype), ('platform', 6, 2)):
            raw = self.thin(subtype=subtype, file_type=file_type)
            path = self.directory / name; path.write_bytes(raw)
            row = self.identity(raw, str(path), 'arm64e' if subtype == 2 else 'arm64')
            images.append(row)
        build['editor'] = {'realpath': images[0]['realpath'], 'sha256': images[0]['sha256'], 'size_bytes': len(self.thin())}
        build['modules'] = [images[1]]
        cached = dict(images[2], realpath='/usr/lib/offline-cache-image.dylib', source='dyld_shared_cache')
        build['external_inputs']['loaded_images'] = sorted(images + [cached], key=lambda row: row['realpath'])
        return build, self.verifier.ExternalFileSnapshot([build['editor']])

    def test_disk_bridge_checks_editor_and_module_types_and_leaves_cache_explicitly_unverified(self):
        build, files = self.build()
        result = self.verifier._build_file_image_relations(self.policy, stored_json_bytes(build), files)
        self.assertEqual(len(result['verified_file_images']), 3)
        self.assertEqual(result['unverified_cache_images'], [build['external_inputs']['loaded_images'][-1]])
        self.assertEqual([row['file_type'] for row in result['verified_file_images']], [2, 6, 6])
        self.assertEqual(result['verified_file_images'][-1]['architecture'], 'arm64e')
        for arguments in ({'editor_type': 6}, {'editor_subtype': 2}, {'module_type': 2}, {'module_subtype': 2}):
            build, files = self.build(**arguments)
            with self.subTest(arguments=arguments), self.assertRaisesRegex(ValueError, '^lcer.image_identity_invalid$'):
                self.verifier._build_file_image_relations(self.policy, stored_json_bytes(build), files)

    def test_consistent_false_image_hash_or_uuid_cannot_authenticate_actual_disk(self):
        for field, value in (('sha256', 'f' * 64), ('macho_uuid', 'f' * 36)):
            build, files = self.build()
            build['modules'][0][field] = value  # Shared row changes both declarations.
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, '^lcer.(external_input_changed|image_identity_invalid)$'):
                self.verifier._build_file_image_relations(self.policy, stored_json_bytes(build), files)

    def test_incomplete_or_duplicated_file_image_census_cannot_pass(self):
        for defect in ('missing_editor', 'missing_module', 'duplicate_image', 'duplicate_module', 'cached_module'):
            build, files = self.build()
            images = build['external_inputs']['loaded_images']
            if defect == 'missing_editor': images.remove(next(row for row in images if row['realpath'] == build['editor']['realpath']))
            elif defect == 'missing_module': images.remove(build['modules'][0])
            elif defect == 'duplicate_image': images.append(dict(images[-1]))
            elif defect == 'duplicate_module': build['modules'].append(dict(build['modules'][0]))
            else: build['modules'][0]['source'] = 'dyld_shared_cache'
            with self.subTest(defect=defect), self.assertRaisesRegex(ValueError, '^lcer.image_identity_invalid$'):
                self.verifier._build_file_image_relations(self.policy, stored_json_bytes(build), files)


class NativeMachOImageTests(unittest.TestCase):
    """Constructed native tables test decoding, never image provenance."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.reader = verifier.NativeMachOImage
        self.base = 0x100000000
        self.name = '_Z_Construct_UClass_Fixturev'

    def image(self):
        raw = bytearray(0x3000)
        commands = []
        for index, name in enumerate((b'__TEXT', b'__DATA', b'__LINKEDIT')):
            sections = int(index < 2)
            command = struct.pack('<II16sQQQQiiII', 0x19, 72 + sections * 80, name,
                                  self.base + index * 0x1000, 0x1000, index * 0x1000, 0x1000,
                                  7, 5 if index == 0 else 3, sections, 0)
            if sections:
                offset = 0x400 if index == 0 else 0x1000
                command += struct.pack('<16s16sQQIIIIIIII', b'__text' if index == 0 else b'__data', name,
                                       self.base + offset, 0x1000 - (offset % 0x1000), offset, 2,
                                       0, 0, 0x80000400 if index == 0 else 0, 0, 0, 0)
            commands.append(command)
        strings = b'\0' + self.name.encode() + b'\0'
        commands.append(struct.pack('<6I', 2, 24, 0x2000, 1, 0x2010, len(strings)))
        commands.append(struct.pack('<II', 0x1b, 24) + bytes(range(16)))
        library = b'@rpath/libFixture.dylib\0'
        library_size = (24 + len(library) + 7) & ~7
        commands.append(struct.pack('<6I', 0xc, library_size, 24, 0, 0, 0) + library.ljust(library_size - 24, b'\0'))
        # Three segment starts. Only __DATA has fixups. Its first pointer
        # rebases to __TEXT; the next binds through the exact import ordinal.
        starts = struct.pack('<4I', 3, 0, 16, 0)
        starts += struct.pack('<IHHQIHH', 24, 0x1000, 6, 0x1000, 0, 1, 0)
        imports_offset = 28 + len(starts)
        fixups = struct.pack('<7I', 0, 28, imports_offset, imports_offset + 4, 1, 1, 0)
        fixups += starts + struct.pack('<I', 1) + b'_Superclass\0'
        commands.append(struct.pack('<4I', 0x80000034, 16, 0x2100, len(fixups)))
        encoded = b''.join(commands)
        raw[:32] = struct.pack('<IiiIIIII', 0xfeedfacf, 0x0100000c, 0, 6, len(commands), len(encoded), 0, 0)
        raw[32:32 + len(encoded)] = encoded
        struct.pack_into('<I', raw, 0x400, 0xd65f03c0)
        raw[0x480:0x488] = 'Pawn'.encode('utf-16le')
        struct.pack_into('<Q', raw, 0x1000, 0x480 | (2 << 51))
        struct.pack_into('<Q', raw, 0x1008, (1 << 63) | (7 << 24))
        raw[0x2000:0x2010] = struct.pack('<IBBHQ', 1, 0xf, 1, 0, self.base + 0x400)
        raw[0x2010:0x2010 + len(strings)] = strings
        raw[0x2100:0x2100 + len(fixups)] = fixups
        return raw

    def decode(self, raw, **changes):
        raw = bytes(raw)
        identity = {'realpath': '/fixture/libNative.dylib', 'sha256': hashlib.sha256(raw).hexdigest(),
                    'macho_uuid': '00010203-0405-0607-0809-0a0b0c0d0e0f',
                    'architecture': 'arm64', 'source': 'dyld'}
        identity.update(changes)
        return self.reader(raw, identity)

    def test_exact_symbol_rebase_import_and_unchained_null(self):
        image = self.decode(self.image())
        self.assertEqual(image.symbol(self.name), self.base + 0x400)
        self.assertEqual(image.read(image.symbol(self.name), 4), b'\xc0\x03\x5f\xd6')
        self.assertEqual(image.pointer(self.base + 0x1000), {'kind': 'rebase', 'address': self.base + 0x480})
        self.assertEqual(image.pointer(self.base + 0x1008),
                         {'kind': 'bind', 'library': '@rpath/libFixture.dylib', 'symbol': '_Superclass', 'addend': 7})
        self.assertEqual(image.pointer(self.base + 0x1010), {'kind': 'null'})

    def test_hash_uuid_architecture_and_cache_source_mismatch_reject(self):
        for changes in ({'sha256': 'a' * 64}, {'macho_uuid': 'unknown'}, {'architecture': 'x86_64'},
                        {'source': 'dyld_shared_cache'}):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
                self.decode(self.image(), **changes)

    def test_zero_string_index_is_unnamed_even_when_first_pool_byte_is_not_nul(self):
        raw = self.image()
        raw[0x2010] = 32
        self.assertEqual(self.decode(raw).symbol(self.name), self.base + 0x400)
        struct.pack_into('<I', raw, 0x2000, 0)
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            self.decode(raw).symbol(' ' + self.name)

    def test_exact_symbol_can_use_a_shared_string_suffix(self):
        raw = self.image()
        strings = b'\0longer' + self.name.encode() + b'\0'
        raw[0x2010:0x2010 + len(strings)] = strings
        struct.pack_into('<I', raw, 0x2000, 7)
        struct.pack_into('<I', raw, 32 + 152 + 152 + 72 + 20, len(strings))
        self.assertEqual(self.decode(raw).symbol(self.name), self.base + 0x400)

    def test_weak_or_duplicate_defined_symbol_cannot_authorize_a_unique_address(self):
        raw = self.image()
        struct.pack_into('<H', raw, 0x2000 + 6, 0x80)
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            self.decode(raw).symbol(self.name)
        raw = self.image()
        strings = b'\0' + self.name.encode() + b'\0'
        raw[0x2010:0x2020] = raw[0x2000:0x2010]
        raw[0x2020:0x2020 + len(strings)] = strings
        command = 32 + 152 + 152 + 72
        struct.pack_into('<III', raw, command + 12, 2, 0x2020, len(strings))
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            self.decode(raw).symbol(self.name)

    def test_symbol_table_partial_rows_keep_the_declared_failure(self):
        for length in range(1, 16):
            image = self.decode(self.image())
            image.symbol_bytes = image.symbol_bytes[:length]
            with self.subTest(length=length), self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
                image.defined_symbols([self.name])
            self.assertEqual(image._symbol_cache, {})

    def test_symbol_table_validates_unrequested_and_debug_string_indexes(self):
        for kind in (0, 0xe0, 0xf):
            raw = self.image()
            struct.pack_into('<IB', raw, 0x2000, 0xffffffff, kind)
            image = self.decode(raw)
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
                image.defined_symbols(['_not_requested_in_table'])
            self.assertEqual(image._symbol_cache, {})

    def test_symbol_table_definition_section_and_address_bounds_are_retained(self):
        for section, description, address in ((0, 0, self.base + 0x400), (3, 0, self.base + 0x400),
                                              (1, 0x80, self.base + 0x400), (1, 0, self.base + 0x3ff),
                                              (1, 0, self.base + 0x1000)):
            raw = self.image()
            struct.pack_into('<BH Q', raw, 0x2000 + 5, section, description, address)
            image = self.decode(raw)
            with self.subTest(section=section, description=description, address=address), self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
                image.defined_symbols([self.name])
            self.assertEqual(image._symbol_cache, {})

    def test_symbol_table_empty_missing_and_cached_results_keep_membership(self):
        image = self.decode(self.image())
        result = image.defined_symbols([self.name, '_Absent'])
        self.assertEqual(result, {self.name: self.base + 0x400})
        self.assertIsNone(image._symbol_cache['_Absent'])
        result[self.name] = -1
        self.assertEqual(image.defined_symbols([self.name, '_Absent']), {self.name: self.base + 0x400})
        empty = self.decode(self.image())
        empty.symbol_bytes = empty.symbol_bytes[:0]
        self.assertEqual(empty.defined_symbols([self.name]), {})
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            empty.symbol(self.name)

    def test_universal_slice_is_selected_by_exact_architecture(self):
        arm = self.image()
        intel = self.image()
        struct.pack_into('<ii', intel, 4, 0x01000007, 3)
        raw = bytearray(0x1000) + arm + intel
        struct.pack_into('>II', raw, 0, 0xcafebabe, 2)
        struct.pack_into('>iiIII', raw, 8, 0x0100000c, 0, 0x1000, len(arm), 12)
        struct.pack_into('>iiIII', raw, 28, 0x01000007, 3, 0x4000, len(intel), 12)
        self.assertEqual(self.decode(raw).symbol(self.name), self.base + 0x400)
        self.assertEqual(self.decode(raw, architecture='x86_64').symbol(self.name), self.base + 0x400)
        struct.pack_into('>I', raw, 36, 0x1000)
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            self.decode(raw)

    def test_unlisted_symbol_unmapped_read_and_unchained_nonzero_reject(self):
        raw = self.image()
        struct.pack_into('<Q', raw, 0x1010, self.base + 0x480)
        image = self.decode(raw)
        for action in (lambda: image.symbol(self.name + '_Near'), lambda: image.read(self.base + 0x3000, 1),
                       lambda: image.pointer(self.base + 0x1010)):
            with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
                action()

    def test_weak_missing_library_and_outside_import_ordinal_reject(self):
        for word, pointer in ((1 | 0x100, (1 << 63)), (2, (1 << 63)), (1, (1 << 63) | 1)):
            raw = self.image()
            struct.pack_into('<I', raw, 0x2100 + 68, word)
            struct.pack_into('<Q', raw, 0x1008, pointer)
            with self.subTest(word=word, pointer=pointer), self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
                self.decode(raw).pointer(self.base + 0x1008)

    def test_unsupported_fixup_format_and_reserved_pointer_bits_reject(self):
        raw = self.image()
        struct.pack_into('<H', raw, 0x2100 + 28 + 16 + 6, 1)
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            self.decode(raw)
        for pointer in (0x480 | (1 << 44), (1 << 63) | (1 << 32)):
            raw = self.image()
            struct.pack_into('<Q', raw, 0x1000, pointer)
            with self.subTest(pointer=pointer), self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
                self.decode(raw).pointer(self.base + 0x1000)

    def test_truncated_tables_and_overlapping_segments_reject(self):
        raw = self.image()
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            self.decode(raw[:0x2104])
        struct.pack_into('<Q', raw, 32 + 152 + 24, self.base)
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            self.decode(raw)


class GeneratedClassDeclarationTests(unittest.TestCase):
    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.parse = verifier.generated_class_declarations
        self.layout = verifier.native_class_parameter_layout
        self.source = b'DECLARE_CLASS2(AExample, AParent, FLAGS(0 | CONFIG), CAST, TEXT("/Script/Example"), Z_Construct_UClass_AExample)'

    def test_nested_macro_arguments_and_physical_line_splices(self):
        raw = b'#define GENERATED_CLASS \\\r\n' + self.source.replace(b', AParent', b', \\\nAParent')
        self.assertEqual(self.parse(raw), [{'cpp_name': 'AExample', 'cpp_parent': 'AParent',
                                           'package': '/Script/Example', 'constructor': 'Z_Construct_UClass_AExample'}])

    def test_comments_and_string_literals_cannot_supply_a_declaration(self):
        self.assertEqual(self.parse(b'// ' + self.source + b'\n/* ' + self.source + b' */\n"DECLARE_CLASS2(fake)"'), [])
        self.assertEqual(self.parse(b'// comment with splice \\\n' + self.source + b'\n'), [])

    def test_changed_constructor_dynamic_package_and_renamed_macro_reject(self):
        for raw in (self.source.replace(b'Z_Construct_UClass_AExample', b'Z_Construct_UClass_AParent'),
                    self.source.replace(b'TEXT("/Script/Example")', b'PackageFromElsewhere()'),
                    b'#define ' + self.source):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
                self.parse(raw)

    def test_duplicate_unbalanced_and_unterminated_inputs_reject(self):
        for raw in (self.source + self.source, self.source[:-1], b'/* ' + self.source,
                    self.source.replace(b'FLAGS(0 | CONFIG)', b'FLAGS([0 | CONFIG)')):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
                self.parse(raw)

    def test_layout_requires_the_exact_pointer_and_bitfield_prefix(self):
        raw = b'''struct FClassParams {
            UClass* (*ClassNoRegisterFunc)(ETypeConstructPhase);
            const char* ClassConfigNameUTF8;
            const FCppClassTypeInfoStatic* CppClassInfo;
            FTypeConstructFunc* const* DependencySingletonFuncArray;
            const FClassFunctionLinkInfo* FunctionLinkArray;
            const FPropertyParamsBase* const* PropertyArray;
            const FImplementedInterfaceParams* ImplementedInterfaceArray;
            uint32 NumDependencySingletons : 4; uint32 NumFunctions : 11;
            uint32 NumProperties : 11; uint32 NumImplementedInterfaces : 6;
        };'''
        self.assertEqual(self.layout(raw), {'self': 0, 'dependencies': 24, 'dependency_count': 56,
                                            'header_sha256': hashlib.sha256(raw).hexdigest()})
        for changed in (raw + raw, raw.replace(b'CppClassInfo;', b'CppClassInfo; void* Extra;'),
                        raw.replace(b'NumDependencySingletons : 4', b'NumDependencySingletons : 5')):
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
                self.layout(changed)


class Arm64ClassRegistrationTests(unittest.TestCase):
    """Raw instruction fixtures exercise the decoder without executing them."""

    def setUp(self):
        self.fixture = NativeMachOImageTests()
        self.fixture.setUp()
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.decoder = verifier.Arm64ClassRegistration
        self.declared = verifier.declared_native_registration
        self.base = self.fixture.base

    def image(self):
        raw = self.fixture.image()
        commands, cursor = [], 32
        count = struct.unpack_from('<I', raw, 16)[0]
        for _ in range(count):
            kind, length = struct.unpack_from('<II', raw, cursor)
            command = bytes(raw[cursor:cursor + length])
            if kind == 0x19 and command[8:24].rstrip(b'\0') == b'__TEXT':
                command = bytearray(command[:72])
                struct.pack_into('<I', command, 4, 72 + 3 * 80)
                struct.pack_into('<I', command, 64, 3)
                for name, offset, size, flags, stub in [(b'__text', 0x400, 0x300, 0x80000400, 0),
                                                        (b'__stubs', 0x700, 24, 8, 12),
                                                        (b'__const', 0x800, 0x800, 0, 0)]:
                    command.extend(struct.pack('<16s16sQQIIIIIIII', name, b'__TEXT', self.base + offset,
                                               size, offset, 2, 0, 0, flags, 0, stub, 0))
            elif kind == 0xc:
                name = self.decoder.LIBRARY.encode() + b'\0'
                length = (24 + len(name) + 7) & ~7
                command = struct.pack('<6I', kind, length, 24, 0, 0, 0) + name.ljust(length - 24, b'\0')
            commands.append(bytes(command))
            cursor += struct.unpack_from('<I', raw, cursor + 4)[0]
        starts = struct.pack('<4I', 3, 0, 16, 0) + struct.pack('<IHHQIHH', 24, 0x1000, 6, 0x1000, 0, 1, 0)
        names = self.decoder.PRIVATE.encode() + b'\0' + self.decoder.CONSTRUCT.encode() + b'\0'
        imports = struct.pack('<II', 1, 1 | ((len(self.decoder.PRIVATE) + 1) << 9))
        fixups = struct.pack('<7I', 0, 28, 68, 76, 2, 1, 0) + starts + imports + names
        commands = [struct.pack('<4I', 0x80000034, 16, 0x2100, len(fixups)) if struct.unpack_from('<I', row)[0] == 0x80000034
                    else row for row in commands]
        commands.append(struct.pack('<4I', 0x26, 16, 0x2400, 8))
        command_bytes = b''.join(commands)
        raw[32:0x400] = command_bytes.ljust(0x400 - 32, b'\0')
        struct.pack_into('<II', raw, 16, len(commands), len(command_bytes))
        raw[0x2100:0x2100 + len(fixups)] = fixups
        raw[0x2400:0x2408] = b'\x80\x08\x80\x06\0\0\0\0'
        struct.pack_into('<Q', raw, 0x1000, (1 << 63) | (2 << 51))
        struct.pack_into('<Q', raw, 0x1008, (1 << 63) | 1 | (62 << 51))
        struct.pack_into('<Q', raw, 0x1100, 0x400)
        for address, offset in ((0x700, 0), (0x70c, 8)):
            struct.pack_into('<III', raw, address, 0xb0000010, 0xf9400210 | ((offset // 8) << 10), 0xd61f0200)
        package, name = '/Script/Fixture'.encode('utf-16le') + b'\0\0', 'PhysicalName'.encode('utf-16le') + b'\0\0'
        raw[0x800:0x800 + len(package)] = package
        raw[0x850:0x850 + len(name)] = name
        words, labels, branches = [], {}, []

        def emit(word, label=None):
            if label:
                labels[label] = 0x400 + 4 * len(words)
            words.append(word)

        def branch(word, label, own=None):
            branches.append((len(words), label))
            emit(word, own)

        emit(0xa9be4ff4); emit(0xa9017bfd); emit(0x910043fd)
        branch(0x34000000, 'inner', 'phase_branch')
        emit(0xb0000013); emit(0x91000000 | (0x208 << 10) | (19 << 5) | 19)
        emit(0xf9400268)
        branch(0xb4000008, 'construct')
        branch(0x14000000, 'exit')
        emit(0xb0000001, 'construct'); emit(0x91000021 | (0x100 << 10))
        emit(0xaa1303e0)
        branch(0x94000000, 'construct_stub', 'construct_call')
        branch(0x14000000, 'exit')
        emit(0xb0000013, 'inner'); emit(0x91000000 | (0x200 << 10) | (19 << 5) | 19)
        emit(0xf9400268)
        branch(0xb5000008, 'exit')
        emit(0x90000000); emit(0x91000000 | (0x800 << 10))
        emit(0x90000001); emit(0x91000021 | (0x850 << 10), 'name_argument')
        emit(0xaa1303e2)
        branch(0x94000000, 'private_stub', 'private_call')
        emit(0xf9400260, 'exit')
        emit(0xa9417bfd); emit(0xa8c24ff4); emit(0xd65f03c0)
        labels.update(private_stub=0x700, construct_stub=0x70c)
        for index, target in branches:
            delta = (labels[target] - (0x400 + 4 * index)) // 4
            if words[index] & 0x7c000000 == 0x14000000:
                words[index] |= delta & 0x3ffffff
            else:
                words[index] |= (delta & 0x7ffff) << 5
        raw[0x400:0x400 + len(words) * 4] = struct.pack('<' + 'I' * len(words), *words)
        return raw, labels

    def decode(self, raw):
        return self.decoder(self.fixture.decode(raw), self.base + 0x400).decode()

    def test_both_phases_and_cache_branches_derive_actual_argument_bytes(self):
        raw, _ = self.image()
        value = self.decode(raw)
        self.assertEqual(value['class_path'], '/Script/Fixture.PhysicalName')
        self.assertEqual(value['class_params'], self.base + 0x1100)
        self.assertEqual(value['inner']['singleton'], self.base + 0x1200)
        self.assertEqual(value['outer']['singleton'], self.base + 0x1208)

    def test_name_comes_from_the_called_literal_not_the_cpp_symbol(self):
        raw, _ = self.image()
        raw[0x850:0x850 + 16] = 'Changed'.encode('utf-16le') + b'\0\0'
        self.assertEqual(self.decode(raw)['reflected_name'], 'Changed')

    def test_dynamic_name_argument_and_wrong_phase_call_reject(self):
        for label, word in [('name_argument', 0xf9400261), ('phase_branch', 0x35000160)]:
            raw, labels = self.image()
            struct.pack_into('<I', raw, labels[label], word)
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, '^lcer.native_registration_unclassified$'):
                self.decode(raw)

    def test_global_store_unknown_opcode_and_escaping_branch_reject(self):
        for word in (0xf9000260, 0x00000000, 0x14000100):
            raw, labels = self.image()
            struct.pack_into('<I', raw, labels['name_argument'], word)
            with self.subTest(word=word), self.assertRaisesRegex(ValueError, '^lcer.native_registration_unclassified$'):
                self.decode(raw)

    def test_returning_a_different_cache_slot_rejects(self):
        raw, labels = self.image()
        struct.pack_into('<I', raw, labels['exit'], 0xf9400660)
        with self.assertRaisesRegex(ValueError, '^lcer.native_registration_unclassified$'):
            self.decode(raw)

    def test_class_params_must_point_back_to_the_actual_constructor(self):
        raw, _ = self.image()
        struct.pack_into('<Q', raw, 0x1100, 0x404)
        with self.assertRaisesRegex(ValueError, '^lcer.native_registration_unclassified$'):
            self.decode(raw)

    def test_function_start_and_stub_structure_are_required(self):
        for offset, replacement in [(0x2400, b'\x84'), (0x700, struct.pack('<I', 0xd503201f))]:
            raw, _ = self.image()
            raw[offset:offset + len(replacement)] = replacement
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
                self.decode(raw)

    def test_declaration_joins_raw_dependency_chain_and_rejects_wrong_package_or_count(self):
        raw, _ = self.image()
        function = 'Z_Construct_UClass_AFixture'
        symbol = '__Z' + str(len(function)) + function + '19ETypeConstructPhase'
        names = b'\0' + symbol.encode() + b'\0'
        raw[0x2010:0x2010 + len(names)] = names
        cursor = 32
        for _ in range(struct.unpack_from('<I', raw, 16)[0]):
            kind, size = struct.unpack_from('<II', raw, cursor)
            if kind == 2:
                struct.pack_into('<I', raw, cursor + 20, len(names))
            cursor += size
        struct.pack_into('<Q', raw, 0x1100, 0x400 | (6 << 51))
        struct.pack_into('<Q', raw, 0x1118, 0x1180 | (26 << 51))
        raw[0x1138] = 2
        struct.pack_into('<Q', raw, 0x1180, 0x500 | (2 << 51))
        struct.pack_into('<Q', raw, 0x1188, 0x520)
        declaration = {'cpp_name': 'AFixture', 'cpp_parent': 'AParent', 'package': '/Script/Fixture',
                       'constructor': function}
        layout = Path('/Users/Shared/Epic Games/UE_5.8/Engine/Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h').read_bytes()
        result = self.declared(self.fixture.decode(raw), declaration, layout)
        self.assertEqual(result['class_path'], '/Script/Fixture.PhysicalName')
        self.assertEqual(result['super_constructor'], {'kind': 'rebase', 'address': self.base + 0x500})
        self.assertEqual(result['package_constructor'], {'kind': 'rebase', 'address': self.base + 0x520})
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            self.declared(self.fixture.decode(raw), dict(declaration, package='/Script/Wrong'), layout)
        raw[0x1138] = 3
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            self.declared(self.fixture.decode(raw), declaration, layout)


class NativePrivateForwardingTests(unittest.TestCase):
    """Actual private-body instructions and rehashed native-byte mutations."""

    @classmethod
    def setUpClass(cls):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        cls.reader, cls.decoder = verifier.NativeMachOImage, verifier.Arm64ClassRegistration
        path = Path('/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/libUnrealEditor-CoreUObject.dylib')
        identity, = [row for row in macho_file_images(path) if row['architecture'] == 'arm64']
        cls.image = cls.reader(path.read_bytes(), identity)
        cls.raw = bytes(cls.image.data)
        cls.field = cls.image.symbol('__Z25Z_Construct_UClass_UField19ETypeConstructPhase')
        cls.private = cls.image.symbol(cls.decoder.PRIVATE)
        cls.private_end = cls.image.function_range(cls.private)[1]
        segment, = [row for row in cls.image.segments if row['address'] <= cls.private < row['address'] + row['file_size']]
        cls.offset = segment['offset'] + cls.private - segment['address']

    @classmethod
    def tearDownClass(cls):
        del cls.image, cls.raw

    def modified(self, changes):
        raw = bytearray(self.raw)
        for word, instruction in changes.items():
            struct.pack_into('<I', raw, self.offset + 4 * word, instruction)
        identity = dict(self.image.identity, sha256=hashlib.sha256(raw).hexdigest())
        return self.reader(bytes(raw), identity)

    def test_actual_optimized_field_constructor_uses_proven_private_helper(self):
        result = self.decoder(self.image, self.field).decode()
        self.assertEqual(result['class_path'], '/Script/CoreUObject.Field')
        self.assertEqual(result['inner']['operation'], 'private')

    def test_scratch_register_renaming_preserves_arguments(self):
        words = struct.unpack('<9I', self.raw[self.offset:self.offset + 36])
        self.assertEqual(self.private_end - self.private, 36)
        image = self.modified({0: (words[0] & ~31) | 2, 7: (words[7] & ~31) | 2,
                               1: (words[1] & ~31) | 10, 6: (words[6] & ~31) | 10})
        self.assertEqual(self.decoder(image, self.field).decode()['class_path'], '/Script/CoreUObject.Field')

    def test_argument_stack_and_control_flow_mutations_reject(self):
        words = struct.unpack('<9I', self.raw[self.offset:self.offset + 36])
        attacks = {
            'store_before_load': {0: words[0] & ~(1 << 22)},
            'integer_argument_clobber': {1: words[1] & ~31},
            'callee_saved_vector_clobber': {2: (words[2] & ~31) | 8},
            'non_stack_base': {3: (words[3] & ~(31 << 5)) | (20 << 5)},
            'changed_stack_argument': {7: words[7] | (1 << 10)},
            'wrong_loaded_bytes': {2: (words[2] & ~(0x1ff << 12)) | (16 << 12)},
            'outside_argument_stack': {1: (words[1] & ~(0xfff << 10)) | (6 << 10)},
            'negative_unscaled_address': {2: (words[2] & ~(0x1ff << 12)) | (0x1f0 << 12)},
            'call_instead_of_tail': {8: words[8] | (1 << 31)},
            'different_target': {8: words[8] + 1},
            'return_instead_of_tail': {8: 0xd65f03c0},
            'unsupported_instruction': {4: 0},
        }
        for name, change in attacks.items():
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, '^lcer.native_registration_unclassified$'):
                self.decoder(self.modified(change), self.field).decode()


class NativeClassInputTests(unittest.TestCase):
    """Native class authority must consume bound files and actual image bytes."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier
        temporary = tempfile.TemporaryDirectory(prefix='city-native-class-inputs-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.engine = Path('/Users/Shared/Epic Games/UE_5.8/Engine')
        paths = [self.engine / 'Intermediate/Build/Mac/UnrealEditor/Inc/Engine/UHT' / (name + '.generated.h')
                 for name in ('Actor', 'Pawn', 'Controller', 'PlayerController')]
        paths.append(self.engine / 'Intermediate/Build/Mac/UnrealEditor/Inc/CoreUObject/UHT/Object.generated.h')
        layout = self.engine / 'Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h'
        self.records = []
        for path in paths + [layout]:
            target = self.root / path.name
            target.write_bytes(path.read_bytes())
            self.records.append(external_file_identity(target))
        self.layout = str(self.root / layout.name)
        self.images = []
        for name in ('CoreUObject', 'Engine'):
            path = self.engine / 'Binaries/Mac' / ('libUnrealEditor-' + name + '.dylib')
            self.images.extend(row for row in macho_file_images(path) if row['architecture'] == 'arm64')

    def read(self, images=None, records=None, files=None):
        records = self.records if records is None else records
        files = self.verifier.ExternalFileSnapshot(records) if files is None else files
        return self.verifier.native_class_inventory(files, self.images if images is None else images, records, self.layout)

    def test_complete_files_and_images_derive_six_class_graph(self):
        registry = self.read()
        self.assertEqual(len(registry.class_parents), 6)
        self.assertEqual(registry.require_classes(['/Script/Engine.Pawn'])['/Script/Engine.Pawn'], '/Script/Engine.Actor')

    def test_missing_parent_image_and_forged_image_identity_reject(self):
        with self.assertRaisesRegex(ValueError, '^lcer.native_ancestry_invalid$'):
            self.read(images=self.images[1:])
        changed = copy.deepcopy(self.images)
        changed[0]['macho_uuid'] = '00000000-0000-0000-0000-000000000000'
        with self.assertRaisesRegex(ValueError, '^lcer.image_identity_invalid$'):
            self.read(images=changed)

    def test_omitted_header_changed_bytes_and_unbound_record_reject(self):
        files = self.verifier.ExternalFileSnapshot(self.records)
        (self.root / 'Pawn.generated.h').write_bytes(b'changed metadata')
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_(changed|invalid)$'):
            self.read(files=files)
        (self.root / 'Pawn.generated.h').unlink()
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_invalid$'):
            self.read()
        changed = copy.deepcopy(self.records)
        changed[0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, '^lcer.native_ancestry_invalid$'):
            self.read(records=changed, files=files)

    def test_nonregistration_image_cannot_hide_malformed_registration_metadata(self):
        path = self.root / 'plain.dylib'
        raw = struct.pack('<IiiIIIII', 0xfeedfacf, 0x0100000c, 0, 6, 1, 24, 0, 0)
        raw += struct.pack('<II', 0x1b, 24) + bytes(range(16))
        path.write_bytes(raw)
        row = {'realpath': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'architecture': 'arm64',
               'macho_uuid': '00010203-0405-0607-0809-0a0b0c0d0e0f', 'source': 'dyld'}
        images = sorted(self.images + [row], key=lambda item: item['realpath'])
        self.assertEqual(len(self.read(images=images).class_parents), 6)
        raw += b'Z_Construct_UClass_Unclassified'
        path.write_bytes(raw)
        row['sha256'] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            self.read(images=images)
        with self.assertRaisesRegex(ValueError, '^lcer.image_identity_invalid$'):
            self.read(images=self.images + [self.images[-1]])


class NativeClassRegistryTests(unittest.TestCase):
    """Installed metadata plus byte mutations; no Unreal execution proof."""

    @classmethod
    def setUpClass(cls):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        cls.reader, cls.registry_type = verifier.NativeMachOImage, verifier.NativeClassRegistry
        engine = Path('/Users/Shared/Epic Games/UE_5.8/Engine')
        cls.images = []
        for module in ('Engine', 'CoreUObject'):
            path = engine / 'Binaries/Mac' / ('libUnrealEditor-' + module + '.dylib')
            identity, = [row for row in macho_file_images(path) if row['architecture'] == 'arm64']
            cls.images.append(cls.reader(path.read_bytes(), identity))
        paths = [engine / 'Intermediate/Build/Mac/UnrealEditor/Inc/Engine/UHT' / (name + '.generated.h')
                 for name in ('Actor', 'Pawn', 'Controller', 'PlayerController')]
        paths.append(engine / 'Intermediate/Build/Mac/UnrealEditor/Inc/CoreUObject/UHT/Object.generated.h')
        cls.layout = str(engine / 'Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h')
        paths.append(Path(cls.layout))
        cls.sources = {str(path): path.read_bytes() for path in paths}
        cls.records = [external_file_identity(path) for path in paths]
        cls.baseline = cls.registry_type(cls.images, cls.records, cls.sources, cls.layout)

    @classmethod
    def tearDownClass(cls):
        del cls.baseline, cls.images, cls.records, cls.sources

    def construct(self, images=None, sources=None, records=None):
        return self.registry_type(self.images if images is None else images, self.records if records is None else records,
                                  self.sources if sources is None else sources, self.layout)

    def changed_header(self, name, before, after):
        sources = dict(self.sources)
        path, = [path for path in sources if path.endswith('/' + name + '.generated.h')]
        self.assertIn(before, sources[path])
        sources[path] = sources[path].replace(before, after)
        records = [dict(row, sha256=hashlib.sha256(sources[path]).hexdigest(), size_bytes=len(sources[path]))
                   if row['realpath'] == path else dict(row) for row in self.records]
        return sources, records

    def changed_engine_pointer(self, address, target):
        image = self.images[0]
        segment, = [row for row in image.segments if row['address'] <= address < row['address'] + row['file_size']]
        offset = segment['offset'] + address - segment['address']
        raw = bytearray(image.data)
        word = struct.unpack_from('<Q', raw, offset)[0]
        self.assertEqual(word >> 63, 0)
        struct.pack_into('<Q', raw, offset, (word & ~((1 << 36) - 1)) | (target - image.base))
        identity = dict(image.identity, sha256=hashlib.sha256(raw).hexdigest())
        return self.reader(bytes(raw), identity)

    def test_all_declared_installed_classes_have_closed_detached_parent_links(self):
        expected = {'/Script/CoreUObject.Object': None, '/Script/Engine.Actor': '/Script/CoreUObject.Object',
                    '/Script/Engine.Pawn': '/Script/Engine.Actor', '/Script/Engine.Controller': '/Script/Engine.Actor',
                    '/Script/Engine.PlayerController': '/Script/Engine.Controller',
                    '/Script/Engine.NoPawnPlayerController': '/Script/Engine.PlayerController'}
        result = self.baseline.require_classes(list(expected))
        self.assertEqual(result, expected)
        result['/Script/Engine.Pawn'] = None
        self.assertEqual(self.baseline.class_parents, expected)

    def test_missing_generated_input_cannot_be_omitted_from_the_supplied_inventory(self):
        sources = dict(self.sources)
        sources.pop(next(path for path in sources if path.endswith('/Pawn.generated.h')))
        with self.assertRaisesRegex(ValueError, '^lcer.native_ancestry_invalid$'):
            self.construct(sources=sources)

    def test_changed_input_bytes_cannot_keep_the_old_hash(self):
        sources = dict(self.sources)
        sources[self.layout] += b'\n// changed\n'
        with self.assertRaisesRegex(ValueError, '^lcer.native_ancestry_invalid$'):
            self.construct(sources=sources)

    def test_rehashed_wrong_parent_declaration_still_rejects(self):
        sources, records = self.changed_header('Pawn', b'DECLARE_CLASS2(APawn, AActor,', b'DECLARE_CLASS2(APawn, AController,')
        with self.assertRaisesRegex(ValueError, '^lcer.native_ancestry_invalid$'):
            self.construct(sources=sources, records=records)

    def test_rehashed_wrong_package_declaration_still_rejects(self):
        sources, records = self.changed_header('Pawn', b'TEXT("/Script/Engine")', b'TEXT("/Script/Wrong")')
        with self.assertRaisesRegex(ValueError, '^lcer.native_metadata_invalid$'):
            self.construct(sources=sources, records=records)

    def test_changed_native_package_pointer_cannot_target_an_unrelated_constructor(self):
        record = self.baseline._records['APawn']
        dependency = self.images[0].pointer(record['class_params'] + 24)['address']
        changed = self.changed_engine_pointer(dependency + 8, self.baseline._records['AActor']['constructor_address'])
        with self.assertRaisesRegex(ValueError, '^lcer.native_ancestry_invalid$'):
            self.construct(images=[changed, self.images[1]])

    def test_consistent_self_parent_declaration_and_pointer_still_reject_as_a_cycle(self):
        sources, records = self.changed_header('Pawn', b'DECLARE_CLASS2(APawn, AActor,', b'DECLARE_CLASS2(APawn, APawn,')
        record = self.baseline._records['APawn']
        dependency = self.images[0].pointer(record['class_params'] + 24)['address']
        changed = self.changed_engine_pointer(dependency, record['constructor_address'])
        with self.assertRaisesRegex(ValueError, '^lcer.native_ancestry_invalid$'):
            self.construct(images=[changed, self.images[1]], sources=sources, records=records)

    def test_a_missing_parent_image_prevents_registry_closure(self):
        with self.assertRaisesRegex(ValueError, '^lcer.native_ancestry_invalid$'):
            self.construct(images=[self.images[0]])

    def test_unavailable_declaration_never_authorizes_a_requested_class(self):
        path = '/fixture/Unused.generated.h'
        raw = b'DECLARE_CLASS2(UUnused, UObject, FLAGS(0), CAST, TEXT("/Script/Unused"), Z_Construct_UClass_UUnused)'
        sources = dict(self.sources, **{path: raw})
        records = self.records + [{'realpath': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)}]
        registry = self.construct(sources=sources, records=records)
        self.assertEqual(registry.class_parents, self.baseline.class_parents)
        with self.assertRaisesRegex(ValueError, '^lcer.native_class_unresolved$'):
            registry.require_classes(['/Script/Unused.Unused'])

    def test_duplicate_native_definition_in_a_different_image_rejects(self):
        image = self.images[0]
        raw = bytearray(image.data)
        cursor = 32
        for _ in range(struct.unpack_from('<I', raw, 16)[0]):
            kind, size = struct.unpack_from('<II', raw, cursor)
            if kind == 0xd:
                offset = struct.unpack_from('<I', raw, cursor + 8)[0]
                name = b'@rpath/duplicate.dylib\0'
                self.assertLessEqual(len(name), size - offset)
                raw[cursor + offset:cursor + size] = name.ljust(size - offset, b'\0')
                break
            cursor += size
        else:
            self.fail('installed image has no dylib ID')
        identity = dict(image.identity, realpath='/fixture/duplicate.dylib', sha256=hashlib.sha256(raw).hexdigest())
        duplicate = self.reader(bytes(raw), identity)
        del raw
        with self.assertRaisesRegex(ValueError, '^lcer.native_ancestry_invalid$'):
            self.construct(images=self.images + [duplicate])


class BuildPythonRelationTests(unittest.TestCase):
    """Raw log/file joins and disk changes, without executing supplied paths."""

    def setUp(self):
        fixture = ExternalFileSnapshotTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture, self.verifier, self.policy = fixture, fixture.verifier, fixture.policy
        self.images = NativeFileImageIdentityTests()
        self.executable = fixture.file('python', self.images.thin(file_type=2))
        self.runtime = {'schema': 'city.live_evidence_python_runtime.v1',
                        'executable': self.executable, 'implementation': 'cpython',
                        'version': '3.14.5 (offline fixture)', 'version_info': [3, 14, 5, 'final', 0]}
        self.compiler = b'compiler output remains byte-exact\r\n\x00\xff\n'
        self.build = schema_example(self.policy['wire_schemas']['build_record'], self.policy['wire_schemas'])
        self.build['external_inputs']['python'] = copy.deepcopy(self.executable)

    def log(self, runtime=None):
        return b'CITY_LCER_PYTHON ' + stored_json_bytes(self.runtime if runtime is None else runtime) + self.compiler

    def verify(self, raw=None, files=None, rehash=True):
        raw = self.log() if raw is None else raw
        if rehash:
            self.build['log'] = {'path': 'build.log', 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)}
        if files is None:
            files = self.verifier.ExternalFileSnapshot([self.build['external_inputs']['python']])
        return self.verifier._build_python_relations(self.policy, stored_json_bytes(self.build), raw, files)

    def test_runtime_header_and_real_file_preserve_compiler_bytes(self):
        for version in ([3, 9, 6, 'final', 0], [3, 14, 5, 'final', 0]):
            self.runtime['version_info'] = version
            result = self.verify()
            self.assertEqual(result['runtime'], self.runtime)
            self.assertEqual(result['compiler_log'], self.compiler)
            self.assertEqual(result['executable_sha256'], self.executable['sha256'])
            self.assertEqual(result['executable_images'][0]['file_type'], 2)
            result['runtime']['version_info'][0] = 99
            self.assertNotEqual(result['runtime'], self.runtime)

    def test_missing_duplicate_and_nonleading_runtime_headers_reject_after_rehash(self):
        line = self.log().split(b'\n', 1)[0]
        for raw in (b'', line, self.compiler, self.compiler + self.log(), self.log() + line + b'\n'):
            with self.subTest(raw=raw[:40]), self.assertRaisesRegex(ValueError, '^lcer.python_runtime_log_invalid$'):
                self.verify(raw)

    def test_noncanonical_duplicate_and_malformed_json_cannot_hide_in_a_valid_log_hash(self):
        payload = stored_json_bytes(self.runtime)
        for raw in (b'CITY_LCER_PYTHON ' + payload.replace(b'{', b'{ ', 1) + self.compiler,
                    b'CITY_LCER_PYTHON {"schema":"duplicate",' + payload[1:] + self.compiler,
                    b'CITY_LCER_PYTHON \xff\n' + self.compiler):
            with self.assertRaises(ValueError):
                self.verify(raw)

    def test_runtime_metadata_shape_rejects_boolean_version_numbers_and_extra_authority(self):
        for key, value in [('schema', 'other'), ('implementation', ''), ('version', ''),
                           ('version_info', [3, True, 5, 'final', 0]),
                           ('version_info', [3, 14, 5, 'final', -1]),
                           ('version_info', [3, 14, 5, 'unknown', 0]),
                           ('version_info', [3, 14, 5]), ('trusted', True)]:
            runtime = copy.deepcopy(self.runtime)
            runtime[key] = value
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, '^lcer.python_runtime_log_invalid$'):
                self.verify(self.log(runtime))

    def test_header_interpreter_must_match_the_declared_and_pinned_identity(self):
        for field, value in [('realpath', self.executable['realpath'] + '-other'),
                             ('sha256', '0' * 64), ('size_bytes', self.executable['size_bytes'] + 1)]:
            runtime = copy.deepcopy(self.runtime)
            runtime['executable'][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, '^lcer.python_runtime_identity_mismatch$'):
                self.verify(self.log(runtime))
        other = self.fixture.file('other', self.images.thin(file_type=2))
        files = self.verifier.ExternalFileSnapshot([other])
        with self.assertRaisesRegex(ValueError, '^lcer.python_runtime_identity_mismatch$'):
            self.verify(files=files)

    def test_changed_executable_bytes_reject_after_snapshot_creation(self):
        files = self.verifier.ExternalFileSnapshot([self.executable])
        Path(self.executable['realpath']).write_bytes(self.images.thin(file_type=6))
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
            self.verify(files=files)

    def test_a_rehashed_library_is_not_an_interpreter_executable(self):
        library = self.fixture.file('library', self.images.thin(file_type=6))
        self.runtime['executable'] = library
        self.build['external_inputs']['python'] = library
        with self.assertRaisesRegex(ValueError, '^lcer.python_runtime_identity_mismatch$'):
            self.verify()

    def test_changed_original_log_rejects_before_runtime_metadata_can_be_accepted(self):
        self.verify()
        with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'):
            self.verify(self.log() + b'changed\n', rehash=False)


class ExternalFileSnapshotTests(unittest.TestCase):
    """Real ordinary files and path attacks; no compiler or Unreal execution."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier
        temporary = tempfile.TemporaryDirectory(prefix='city-external-files-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.policy = json.loads(CONTRACT_PATH.read_bytes())

    def file(self, name, raw):
        path = self.directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {'realpath': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)}

    def test_current_bytes_empty_file_and_shared_role_identity(self):
        first = self.file('inputs/first', b'actual input\n')
        empty = self.file('inputs/empty', b'')
        snapshot = self.verifier.ExternalFileSnapshot([first, empty, dict(first)])
        self.assertEqual(snapshot.read(first['realpath']), b'actual input\n')
        self.assertEqual(snapshot.read(empty['realpath']), b'')
        first['sha256'] = '0' * 64  # Caller changes cannot alter the pinned record.
        snapshot.verify()
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_invalid$'):
            snapshot.read(str(self.directory / 'unlisted'))

    def test_repeated_metadata_cannot_authenticate_different_disk_bytes(self):
        first = self.file('input', b'original')
        for change in ({'sha256': '0' * 64}, {'size_bytes': 9}, {'size_bytes': True}, {'extra': True}):
            bad = dict(first, **change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^lcer.external_input_(invalid|changed)$'):
                self.verifier.ExternalFileSnapshot([bad, dict(bad)])
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_invalid$'):
            self.verifier.ExternalFileSnapshot([first, dict(first, sha256='0' * 64)])

    def test_missing_symlink_ancestor_directory_and_fifo_are_denied_without_following(self):
        first = self.file('actual/input', b'bytes')
        alias = self.directory / 'alias'; alias.symlink_to(self.directory / 'actual', target_is_directory=True)
        leaf = self.directory / 'leaf'; leaf.symlink_to(first['realpath'])
        fifo = self.directory / 'fifo'; os.mkfifo(fifo)
        for path in (self.directory / 'missing', alias / 'input', leaf, self.directory / 'actual', fifo):
            with self.subTest(path=str(path)), self.assertRaisesRegex(ValueError, '^lcer.external_input_(invalid|changed)$'):
                self.verifier.ExternalFileSnapshot([dict(first, realpath=str(path))])

    def test_noncanonical_paths_cannot_alias_a_record(self):
        first = self.file('input', b'bytes')
        for path in ('input', '/', first['realpath'] + '/', str(self.directory) + '//input',
                     str(self.directory) + '/nested/../input', first['realpath'] + '\0suffix'):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, '^lcer.external_input_invalid$'):
                self.verifier.ExternalFileSnapshot([dict(first, realpath=path)])

    def test_consumption_and_final_verification_reread_the_actual_file(self):
        first = self.file('input', b'first bytes')
        snapshot = self.verifier.ExternalFileSnapshot([first])
        Path(first['realpath']).write_bytes(b'other bytes')
        for action in (lambda: snapshot.read(first['realpath']), snapshot.verify):
            with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
                action()

    def test_descriptor_reader_is_bounded_and_cannot_outlive_its_context(self):
        first = self.file('input', b'0123456789')
        snapshot = self.verifier.ExternalFileSnapshot([first])
        with snapshot.reader(first['realpath']) as read:
            self.assertEqual(read(3, 4), b'3456')
            self.assertEqual(read(10, 0), b'')
            for offset, count in ((-1, 1), (10, 1), (0, 11), (True, 1), (0, False)):
                with self.assertRaisesRegex(ValueError, '^lcer.external_input_invalid$'):
                    read(offset, count)
        with self.assertRaisesRegex(ValueError, '^lcer.external_input_invalid$'):
            read(0, 1)

    def test_descriptor_reader_detects_changed_and_truncated_bytes_on_exit(self):
        for changed in (b'other bytes', b''):
            first = self.file('input', b'first bytes')
            snapshot = self.verifier.ExternalFileSnapshot([first])
            with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
                with snapshot.reader(first['realpath']) as read:
                    self.assertEqual(read(0, 5), b'first')
                    Path(first['realpath']).write_bytes(changed)

    def test_mutation_and_ancestor_replacement_during_read_are_detected(self):
        first = self.file('inputs/input', b'a' * (1048576 + 10))
        original_read = self.verifier.os.read
        for attack in ('content', 'ancestor'):
            path = Path(first['realpath'])
            fired = []
            def changed_read(descriptor, count):
                raw = original_read(descriptor, count)
                if not fired:
                    fired.append(True)
                    if attack == 'content':
                        path.write_bytes(b'b' * first['size_bytes'])
                    else:
                        path.parent.rename(self.directory / 'moved')
                        path.parent.mkdir()
                        path.write_bytes(b'a' * first['size_bytes'])
                return raw
            with self.subTest(attack=attack), mock.patch.object(self.verifier.os, 'read', side_effect=changed_read):
                with self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
                    self.verifier.ExternalFileSnapshot([first])
            self.assertEqual(fired, [True])
            path.write_bytes(b'a' * first['size_bytes'])

    def test_build_file_slots_are_all_read_and_conflicting_roles_reject(self):
        build = schema_example(self.policy['wire_schemas']['build_record'], self.policy['wire_schemas'])
        external = build['external_inputs']
        for key in ('editor', 'project'):
            build[key] = self.file(key, key.encode())
        for key in ('engine_build_version', 'compiler', 'sdk', 'python', 'dyld_cache'):
            external[key] = self.file(key, key.encode())
        for key in ('build_inputs', 'engine_configs', 'engine_plugins'):
            external[key] = [self.file(key + '/first', key.encode()), self.file(key + '/second', b'second')]
        snapshot = self.verifier._build_file_relations(self.policy, stored_json_bytes(build))
        self.assertEqual(len(snapshot._records), 13)
        for key in ('build_inputs', 'engine_configs', 'engine_plugins'):
            for defect in ('empty', 'duplicate', 'reordered', 'conflict'):
                changed = copy.deepcopy(build)
                rows = changed['external_inputs'][key]
                if defect == 'empty': rows.clear()
                elif defect == 'duplicate': rows.append(dict(rows[-1]))
                elif defect == 'reordered': rows.reverse()
                else: rows[0] = dict(build['editor'], sha256='f' * 64); rows.sort(key=lambda row: row['realpath'])
                with self.subTest(key=key, defect=defect), self.assertRaisesRegex(ValueError, '^lcer.external_input_invalid$'):
                    self.verifier._build_file_relations(self.policy, stored_json_bytes(changed))
        for row in list(snapshot._records.values()):
            path = Path(row['realpath']); raw = path.read_bytes()
            path.write_bytes(b'changed')
            with self.subTest(path=str(path)), self.assertRaisesRegex(ValueError, '^lcer.external_input_changed$'):
                self.verifier._build_file_relations(self.policy, stored_json_bytes(build))
            path.write_bytes(raw)


class SourceIdentityRelationTests(unittest.TestCase):
    """Real disposable Git objects and current CITY byte comparisons only."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier
        temporary = tempfile.TemporaryDirectory(prefix='city-git-identity-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.repository = self.directory / 'repository'
        self.repository.mkdir()
        self.environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
                            'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_AUTHOR_NAME': 'Offline Fixture',
                            'GIT_AUTHOR_EMAIL': 'fixture@example.invalid', 'GIT_COMMITTER_NAME': 'Offline Fixture',
                            'GIT_COMMITTER_EMAIL': 'fixture@example.invalid'}
        self.git('init', '--template=', '-q')
        (self.repository / 'value.txt').write_text('first\n')
        self.git('add', 'value.txt')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-q', '-m', 'First fixture')
        self.first = {'source_commit': self.git('rev-parse', 'HEAD').decode().strip(),
                      'source_tree': self.git('rev-parse', 'HEAD^{tree}').decode().strip()}

    def git(self, *arguments):
        return subprocess.check_output(['/usr/bin/git', *arguments], cwd=self.repository, env=self.environment,
                                       stderr=subprocess.PIPE, timeout=15)

    def second_commit(self):
        (self.repository / 'value.txt').write_text('second\n')
        self.git('add', 'value.txt')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-q', '-m', 'Second fixture')
        return {'source_commit': self.git('rev-parse', 'HEAD').decode().strip(),
                'source_tree': self.git('rev-parse', 'HEAD^{tree}').decode().strip()}

    def context(self):
        policy = json.loads(CONTRACT_PATH.read_bytes())
        city = CONTRACT_PATH.parent.parent
        prefix = policy['runtime']['output_root'] + '/'
        sources = {name: (city / name).read_bytes() for name in policy['release_members'] if not name.startswith(prefix)}
        identity = self.verifier._current_git_identity(city)
        build = schema_example(policy['wire_schemas']['build_record'], policy['wire_schemas'])
        acquisition = schema_example(policy['wire_schemas']['acquisition_record'], policy['wire_schemas'])
        build.update(identity); acquisition.update(identity)
        return {'policy': policy, 'root': self.directory / 'copied-release', 'source_bytes': sources,
                'artifacts': {'build.json': stored_json_bytes(build), 'acquisition.json': stored_json_bytes(acquisition)}}

    def test_actual_commit_object_and_tree_are_bound_without_claiming_dirty_files_committed(self):
        self.assertEqual(self.verifier._current_git_identity(self.repository), self.first)
        (self.repository / 'value.txt').write_text('uncommitted candidate\n')
        self.assertEqual(self.verifier._current_git_identity(self.repository), self.first)
        second = self.second_commit()
        self.assertNotEqual(second, self.first)
        self.assertEqual(self.verifier._current_git_identity(self.repository), second)

    def test_actual_git_replacement_cannot_substitute_another_commit_tree(self):
        second = self.second_commit()
        self.git('update-ref', 'HEAD', self.first['source_commit'])
        self.git('replace', self.first['source_commit'], second['source_commit'])
        self.assertEqual(self.git('rev-parse', 'HEAD^{tree}').decode().strip(), second['source_tree'])
        self.assertEqual(self.verifier._current_git_identity(self.repository), self.first)

    def test_corrupted_loose_tree_cannot_keep_its_recorded_object_identity(self):
        tree_id = self.first['source_tree']
        tree = self.git('cat-file', 'tree', tree_id)
        # Keep the Git tree structure valid while changing its referenced blob.
        changed = tree[:-1] + bytes([tree[-1] ^ 1])
        self.assertNotEqual(tree, changed)
        loose = self.repository / '.git/objects' / tree_id[:2] / tree_id[2:]
        loose.chmod(0o600)
        loose.write_bytes(zlib.compress(b'tree ' + str(len(changed)).encode('ascii') + b'\0' + changed))
        # Git may reject the corrupt object while resolving HEAD^{tree},
        # before the verifier reaches its independent raw-object hash check.
        with self.assertRaisesRegex(ValueError, '^lcer.source_git_identity_invalid$'):
            self.verifier._current_git_identity(self.repository)

    def test_inherited_git_environment_cannot_redirect_repository_identity(self):
        fake = self.directory / 'unrelated-git'
        with mock.patch.dict(os.environ, {'GIT_DIR': str(fake), 'GIT_WORK_TREE': str(fake),
                                          'GIT_OBJECT_DIRECTORY': str(fake), 'GIT_COMMON_DIR': str(fake),
                                          'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.bare', 'GIT_CONFIG_VALUE_0': 'true'}):
            self.assertEqual(self.verifier._current_git_identity(self.repository), self.first)

    def test_nonrepository_subdirectory_and_symlink_cannot_name_another_git_root(self):
        empty = self.directory / 'empty'; empty.mkdir()
        subdirectory = self.repository / 'nested'; subdirectory.mkdir()
        alias = self.directory / 'alias'; alias.symlink_to(self.repository, target_is_directory=True)
        for path in (empty, subdirectory, alias):
            with self.subTest(path=str(path)), self.assertRaisesRegex(ValueError, '^lcer.source_git_identity_invalid$'):
                self.verifier._current_git_identity(path)

    def test_actual_city_identity_and_all_seventy_current_bytes_pass_for_a_copy(self):
        context = self.context()
        self.assertEqual(len(context['source_bytes']), 70)
        result = self.verifier._source_identity_relations(context)
        self.assertEqual(result, self.verifier._current_git_identity(CONTRACT_PATH.parent.parent))
        self.assertFalse(context['root'].exists())  # The copy's path supplies no Git authority.

    def test_matching_fabricated_or_mixed_recorded_git_identities_reject(self):
        original = self.context()
        for field in ('source_commit', 'source_tree'):
            for labels in (('build.json',), ('build.json', 'acquisition.json')):
                context = copy.deepcopy(original)
                for label in labels:
                    record = json.loads(context['artifacts'][label]); record[field] = 'f' * 40
                    context['artifacts'][label] = stored_json_bytes(record)
                with self.subTest(field=field, labels=labels), self.assertRaisesRegex(ValueError, '^lcer.source_identity_mismatch$'):
                    self.verifier._source_identity_relations(context)

    def test_missing_extra_or_changed_release_source_cannot_keep_git_provenance(self):
        original = self.context()
        for defect in ('missing', 'extra', 'changed'):
            context = copy.deepcopy(original)
            name = 'proof_kernel/live_cross_domain_evidence_round_trip_harness.py'
            if defect == 'missing': del context['source_bytes'][name]
            elif defect == 'extra': context['source_bytes']['unlisted.py'] = b'pass\n'
            else: context['source_bytes'][name] += b'\n# changed copy\n'
            with self.subTest(defect=defect), self.assertRaisesRegex(ValueError, '^lcer.source_identity_mismatch$'):
                self.verifier._source_identity_relations(context)


class AcquisitionRelationTests(unittest.TestCase):
    """Complete typed acquisition graph; no compiler, kernel or live claims."""

    def setUp(self):
        fixture = CaseLaunchRelationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture, self.verifier, self.policy = fixture, fixture.verifier, fixture.policy
        self.names = self.policy['artifact_hash_graph']['case_ids']
        self.artifacts = {name: b'typed artifact graph fixture; not live evidence\n' for name in self.policy['artifact_relative_paths']}
        for role in ('R0', 'R1', 'QA', 'QB'):
            self.artifacts['canonical/' + role + '.json'] = (CONTRACT_PATH.parent / 'ConcurrentExternalEvidenceArbitrationProofRecords' /
                ('concurrent_external_' + role + '.json')).read_bytes()
        self.build = copy.deepcopy(fixture.build)
        self.build.update(source_commit='a' * 40, source_tree='b' * 40)
        self.results = {}; self.cases = {}
        witnesses = {row['id'] for row in self.policy['witnesses']}
        programs = {row['id']: row for row in self.policy['failure_programs']}
        canonical_codes = {'C%02d' % (index + 1): self.policy['canonical_fault_codes'][point]
                           for index, point in enumerate(self.policy['canonical_faults'])}
        for index, name in enumerate(self.names):
            fixture.make_case(name)
            for number, process in enumerate(fixture.processes):
                process['pid'] = 10000 + index * 3 + number
                process['startup'].update(pid=process['pid'], launch_id=name + '_launch_%d' % number)
                for descriptor in process['descriptors']: descriptor['pid'] = process['pid']
                fixture.launch_tuple(process, process['environment']['HOME'][:-5])
            partial, trace = fixture.records()
            launches = fixture.check(partial, trace)
            is_witness = name in witnesses
            published = is_witness or (name in programs and programs[name]['prefix'] in ('P3', 'P4', 'P5'))
            failures = [] if is_witness else [canonical_codes[name]] if name in canonical_codes else [
                next(family['failure_code'] for family in self.policy['failure_cases'] if name in family['runs'])]
            outcome = {'status': 'accepted' if is_witness else 'expected_failure', 'failure_codes': failures,
                       'claims': {'synchronized_representation': is_witness, 'canonical_commit': published,
                                  'production_ready': False, 'trusted_ci': False, 'game_sealed': False}}
            case = schema_example(self.policy['wire_schemas']['case_record'], self.policy['wire_schemas'])
            case.update(partial, **copy.deepcopy(outcome), canonical_artifacts={
                'initial_raw_utf8': self.artifacts['canonical/R0.json'].decode(),
                'published_raw_utf8': self.artifacts['canonical/R1.json'].decode() if published else None,
                'terminal_raw_utf8': self.artifacts['canonical/R1.json' if published else 'canonical/R0.json'].decode()})
            self.cases[name] = case
            self.results[name] = {'outcome': outcome, 'launches': launches}
        self.acquisition = schema_example(self.policy['wire_schemas']['acquisition_record'], self.policy['wire_schemas'])
        self.acquisition.update(source_commit=self.build['source_commit'], source_tree=self.build['source_tree'], status='complete',
            claims={'synchronized_representation': True, 'canonical_commit': True, 'production_ready': False, 'trusted_ci': False, 'game_sealed': False})
        self.refresh()

    def index(self, name):
        raw = self.artifacts[name]
        return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)}

    def refresh(self):
        graph = self.policy['artifact_hash_graph']
        for name, case in self.cases.items():
            case['artifact_sha256'] = [self.index(path) for path in graph['case_record_targets'][name]]
            self.artifacts[name + '/record.json'] = stored_json_bytes(case)
        self.build['log'] = self.index('build.log')
        self.artifacts['build.json'] = stored_json_bytes(self.build)
        self.acquisition.update(build_sha256=self.index('build.json')['sha256'], artifact_members=self.policy['artifact_relative_paths'],
            artifact_hashes=[self.index(name) for name in graph['acquisition_targets']],
            cases=[{'witness_id': name, 'record_path': name + '/record.json',
                    'record_sha256': self.index(name + '/record.json')['sha256']} for name in self.names])
        self.artifacts['acquisition.json'] = stored_json_bytes(self.acquisition)

    def check(self, results=None, artifacts=None):
        return self.verifier._acquisition_relations(self.policy, self.artifacts if artifacts is None else artifacts,
                                                    self.results if results is None else results)

    def change_identity(self, name, field, value, number=0):
        row = self.results[name]['launches'][number]
        original = row['launch_id']
        row[field] = copy.deepcopy(value)
        for binding in self.cases[name]['process_bindings']:
            if binding['launch_id'] == original and field in binding: binding[field] = copy.deepcopy(value)
        self.refresh()

    def test_all_cases_and_71_launches_produce_only_frozen_bounded_claims(self):
        result = self.check()
        self.assertEqual(result['case_ids'], self.names)
        self.assertEqual(len(result['launches']), 71)
        self.assertEqual(result['synchronized_cases'], ['W%d' % number for number in range(1, 9)])
        self.assertEqual(len(result['publication_cases']), 19)
        self.assertFalse(any(result['claims'][name] for name in ('production_ready', 'trusted_ci', 'game_sealed')))

    def test_missing_extra_or_reordered_case_results_cannot_complete_acquisition(self):
        for name in ('W1', 'F07', 'C06'):
            results = copy.deepcopy(self.results); del results[name]
            with self.subTest(missing=name), self.assertRaises(ValueError): self.check(results=results)
        for results in (dict(reversed(list(self.results.items()))), dict(self.results, extra=self.results['W1'])):
            with self.assertRaises(ValueError): self.check(results=results)

    def test_cross_case_launch_parent_and_user_identity_conflicts_reject(self):
        before = copy.deepcopy((self.results, self.cases))
        for field, value in [('launch_id', self.results['W1']['launches'][0]['launch_id']), ('ppid', 98765), ('operator_user', 'different_user')]:
            self.results, self.cases = copy.deepcopy(before)
            self.change_identity('W2', field, value)
            with self.subTest(field=field), self.assertRaises(ValueError): self.check()

    def test_pid_reuse_requires_distinct_birth_identity(self):
        original = self.results['W1']['launches'][0]
        self.change_identity('W2', 'pid', original['pid'])
        self.change_identity('W2', 'macos_birth_tuple', dict(original['macos_birth_tuple'], seconds=original['macos_birth_tuple']['seconds'] + 1))
        self.check()
        self.change_identity('W2', 'macos_birth_tuple', original['macos_birth_tuple'])
        with self.assertRaises(ValueError): self.check()

    def test_rehashed_shared_nested_relative_or_noncanonical_roots_reject(self):
        before = copy.deepcopy((self.results, self.cases))
        root = self.results['W1']['launches'][0]['process_root_realpath']
        for value in (root, root + '/nested', 'relative/root', root + '/../alias'):
            self.results, self.cases = copy.deepcopy(before)
            self.change_identity('W2', 'process_root_realpath', value)
            with self.subTest(root=value), self.assertRaises(ValueError): self.check()

    def test_f07_replacement_cannot_be_omitted_substituted_or_rebound(self):
        before = copy.deepcopy(self.results)
        for defect in ('missing', 'peer', 'original', 'wrong_case'):
            results = copy.deepcopy(before)
            rows = results['F07']['launches']
            bindings = {row['launch_id'] for row in self.cases['F07']['process_bindings']}
            replacement = next(row for row in rows if row['launch_id'] not in bindings)
            if defect == 'missing': rows.remove(replacement)
            elif defect == 'peer': replacement['domain'] = 'domain_B'
            elif defect == 'original': replacement['launch_id'] = next(iter(bindings))
            else: replacement['witness_id'] = 'W1'
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.check(results=results)

    def test_case_and_acquisition_status_claims_and_source_identity_are_checked(self):
        before = copy.deepcopy((self.results, self.cases, self.build, self.acquisition))
        for defect in ('case_status', 'case_failure', 'case_commit', 'acquisition_status', 'acquisition_claim', 'broader_claim', 'commit', 'tree', 'malformed_identity'):
            self.results, self.cases, self.build, self.acquisition = copy.deepcopy(before)
            if defect.startswith('case_'):
                outcome = self.results['F01']['outcome']
                if defect == 'case_status': outcome['status'] = 'accepted'
                elif defect == 'case_failure': outcome['failure_codes'] = []
                else: outcome['claims']['canonical_commit'] = True
                self.cases['F01'].update(copy.deepcopy(outcome))
            elif defect == 'acquisition_status': self.acquisition['status'] = 'failed'
            elif defect == 'acquisition_claim': self.acquisition['claims']['synchronized_representation'] = False
            elif defect == 'broader_claim': self.acquisition['claims']['trusted_ci'] = True
            elif defect == 'commit': self.build['source_commit'] = 'c' * 40
            elif defect == 'tree': self.build['source_tree'] = 'c' * 40
            else: self.build['source_commit'] = self.acquisition['source_commit'] = 'not-a-commit'
            self.refresh()
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.check()

    def test_rehashed_case_swap_and_stale_backward_edges_reject(self):
        original = copy.deepcopy(self.artifacts)
        for defect in ('case_identity', 'record_path', 'record_hash', 'build_hash'):
            self.artifacts = copy.deepcopy(original)
            if defect == 'case_identity':
                self.cases['W1']['witness_id'] = 'W2'
                self.refresh()
                self.cases['W1']['witness_id'] = 'W1'
            else:
                acquisition = json.loads(self.artifacts['acquisition.json'])
                if defect == 'record_path': acquisition['cases'][0]['record_path'] = 'W2/record.json'
                elif defect == 'record_hash': acquisition['cases'][0]['record_sha256'] = acquisition['cases'][1]['record_sha256']
                else: acquisition['build_sha256'] = 'f' * 64
                self.artifacts['acquisition.json'] = stored_json_bytes(acquisition)
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.check()

    def test_release_protocol_does_not_accept_supplied_green_case_flags(self):
        fixture = OperationScheduleRelationTests()
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.make_case('W1'); fixture.verify()
        self.check()  # The separate typed aggregate is internally consistent.
        artifacts = dict(self.artifacts, **fixture.artifacts)
        artifacts['W1/record.json'] = stored_json_bytes(fixture.case)
        context = {'policy': self.policy, 'artifacts': artifacts, 'source_bytes': self.fixture.sources,
                   'case_results': self.results}
        with self.assertRaisesRegex(ValueError, '^lcer.original_pipe_identity_mismatch$'):
            self.verifier._release_protocol_relations(context, fixture.fixture.canonical)


class PublicReleaseIntegrationTests(unittest.TestCase):
    """Real verifier CLI over hashed offline records, never live acceptance."""

    def setUp(self):
        self.release = ReleaseBootstrapTests()
        self.release.setUp()
        self.addCleanup(self.release.doCleanups)
        self.schedule = OperationScheduleRelationTests()
        self.schedule.setUp()
        self.addCleanup(self.schedule.doCleanups)
        self.schedule.make_case('W1')
        # The actual parent/canonical fixture supplies coherent raw streams
        # and order. Its simulated process records have no original pipes.
        self.schedule.verify()
        self.install_case()

    def install_case(self):
        self.release.cases['W1'] = copy.deepcopy(self.schedule.case)
        for name, raw in self.schedule.artifacts.items():
            (self.release.artifacts / name).write_bytes(raw)
        self.release.refresh_graph()
        context = self.release.bootstrap.authenticate_release(self.release.root, self.release.artifacts)
        self.assertEqual(len(context['members']), 289)

    def invoke(self):
        files = [path for root in (self.release.root, self.release.artifacts)
                 for path in root.rglob('*') if path.is_file()]
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
        argv = [sys.executable, '-B', 'proof_kernel/verify_live_cross_domain_evidence_round_trip_release.py',
                'verify', '--artifacts', str(self.release.artifacts)]
        result = subprocess.run(argv, cwd=self.release.root, capture_output=True, timeout=30)
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                 for root in (self.release.root, self.release.artifacts)
                 for path in root.rglob('*') if path.is_file()}
        self.assertEqual(after, before)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.last_command = {'argv': argv, 'cwd': str(self.release.root), 'exit_code': result.returncode,
                             'stdout': result.stdout, 'stderr': result.stderr, 'source_and_artifacts_unchanged': True}
        return json.loads(result.stdout)

    def test_normal_verifier_reaches_original_pipe_checks_after_valid_raw_order(self):
        self.assertEqual(self.invoke(), {'status': 'fail',
                         'failure_codes': ['lcer.original_pipe_identity_mismatch']})

    def test_normal_verifier_rejects_rehashed_case_timeout_before_process_checks(self):
        self.schedule.events[-1]['monotonic_ns'] = self.schedule.events[0]['monotonic_ns'] + 901 * 10**9
        self.schedule.sync(keep_clock=True)
        self.install_case()
        self.assertEqual(self.invoke(), {'status': 'fail', 'failure_codes': ['lcer.case_timeout']})

    def test_normal_verifier_parses_raw_trace_even_when_all_hashes_match(self):
        path = self.release.artifacts / 'W1/harness.jsonl'
        lines = path.read_bytes().splitlines(keepends=True)
        event = json.loads(lines[0])
        event['undeclared'] = 'a hash does not make this a valid trace event'
        lines[0] = stored_json_bytes(event)
        path.write_bytes(b''.join(lines))
        self.release.refresh_graph()
        self.release.bootstrap.authenticate_release(self.release.root, self.release.artifacts)
        self.assertEqual(self.invoke(), {'status': 'fail', 'failure_codes': ['lcer.schema_invalid']})


class CaseLaunchRelationTests(unittest.TestCase):
    """Typed build/process records exercise joins, never compilation or launch."""

    def setUp(self):
        fixture = ProcessBindingRelationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.verifier, self.policy = fixture.verifier, fixture.policy
        self.parents = fixture.parents
        self.base = Path('/Users/boandersson/Projects/CITY')
        fixture.startup['proof_module']['realpath'] = str(self.base / self.policy['runtime']['plugin'] /
            'Binaries/Mac/libUnrealEditor-CityLiveEvidenceProof.dylib')
        prefix = str(Path(self.policy['runtime']['project']).parent) + '/Config/'
        self.config_names = sorted(name for name in self.policy['unchanged_dependencies'] if name.startswith(prefix))
        names = self.config_names + [self.policy['runtime']['project'], self.policy['runtime']['plugin'] + '/CityLiveEvidenceProof.uplugin']
        self.sources = {name: (self.base / name).read_bytes() for name in names}

        def file(name):
            raw = self.sources[name]
            return {'realpath': str(self.base / name), 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)}

        self.build = schema_example(self.policy['wire_schemas']['build_record'], self.policy['wire_schemas'])
        self.build.update(argv=[value.format(absolute_city_project=str(self.base / self.policy['runtime']['project'])) for value in self.policy['build_argv']],
                          cwd=str(self.base), returncode=0, project=file(self.policy['runtime']['project']),
                          editor=copy.deepcopy(fixture.observation['executable']), modules=[copy.deepcopy(fixture.startup['proof_module'])])
        editor_image = dict(self.build['modules'][0], realpath=self.build['editor']['realpath'], sha256=self.build['editor']['sha256'])
        self.build['external_inputs'].update(build_inputs=[file(name) for name in sorted(names)],
            engine_configs=[file(name) for name in self.config_names],
            engine_plugins=[file(self.policy['runtime']['plugin'] + '/CityLiveEvidenceProof.uplugin')],
            loaded_images=sorted([editor_image, copy.deepcopy(self.build['modules'][0])], key=lambda row: row['realpath']))
        self.make_case('W1')

    def make_case(self, name):
        self.name = name
        self.processes = []
        for number in range(3 if name == 'F07' else 2):
            process = copy.deepcopy(self.fixture.observation)
            process['pid'] += number
            startup = process['startup']
            startup.update(witness_id=name, domain='domain_B' if number == 1 else 'domain_A',
                           launch_id='offline_launch_%d' % number, pid=process['pid'],
                           proof_module=copy.deepcopy(self.build['modules'][0]),
                           config_files=copy.deepcopy(self.build['external_inputs']['engine_configs']),
                           enabled_plugins=copy.deepcopy(self.build['external_inputs']['engine_plugins']),
                           loaded_images=copy.deepcopy(self.build['external_inputs']['loaded_images']))
            process['loaded_images'] = copy.deepcopy(startup['loaded_images'])
            for row in process['descriptors']:
                row['pid'] = process['pid']; row['kernel_id'] += '_%d' % number; row['peer_kernel_id'] += '_%d' % number
            self.launch_tuple(process, '/private/tmp/offline-launch-inputs/%s/launch_%d' % (name, number))
            self.processes.append(process)

    def launch_tuple(self, process, root, user='offline_operator'):
        startup = process['startup']
        values = dict(engine=self.policy['runtime']['engine'], absolute_city_project=self.build['project']['realpath'],
                      absolute_domain_root=root, observed_operator_user=user, witness_id=startup['witness_id'],
                      domain=startup['domain'], launch_id=startup['launch_id'])
        process['argv'] = [value.format_map(values) for value in self.policy['launch_argv']]
        process['environment'] = {key: value.format_map(values) for key, value in self.policy['launch_environment'].items()}

    def records(self):
        bindings = []; events = []
        for number, process in enumerate(self.processes):
            startup = process['startup']; domain = startup['domain']
            events.append({'event_id': 'wire_event', 'payload': {'parsed_schema': 'startup', 'raw_line_utf8': stored_json_bytes(startup).decode()}})
            sample = {'checkpoint': 'startup' if number < 2 else 'terminal', 'domain': domain,
                      'launch_id': startup['launch_id'], 'observed_process': process}
            if number < 2:
                root = process['environment']['HOME'][:-5]
                bindings.append(process_binding_from_observation(self.fixture.contract_raw, stored_json_bytes(startup), process,
                    self.build['project'], root, process['environment']['USER']))
                events.append({'event_id': 'liveness', 'payload': sample})
            else:
                events.append({'event_id': 'fault_event', 'payload': {'failure_case': 'F07', 'after': {'kind': 'process', 'sample': sample}}})
        return {'witness_id': self.name, 'process_bindings': bindings}, {'events': events}

    def check(self, case=None, trace=None, build=None, sources=None):
        if case is None: case, trace = self.records()
        return self.verifier._case_launch_relations(self.policy, case, trace, self.build if build is None else build,
            self.sources if sources is None else sources, self.parents)

    def test_originals_and_unbound_replacement_join_exact_build_inputs(self):
        for name, count in [('W1', 2), ('F07', 3)]:
            self.make_case(name)
            rows = self.check()
            self.assertEqual(len(rows), count)
            self.assertEqual({row['launch_id'] for row in rows}, {process['startup']['launch_id'] for process in self.processes})

    def test_arm64e_platform_images_join_an_arm64_editor_and_proof_module(self):
        cached = dict(self.build['modules'][0], realpath='/usr/lib/offline-cache-image.dylib',
                      architecture='arm64e', source='dyld_shared_cache')
        self.build['external_inputs']['loaded_images'].append(cached)
        self.build['external_inputs']['loaded_images'].sort(key=lambda row: row['realpath'])
        self.make_case('W1')
        self.assertEqual(len(self.check()), 2)
        for architecture in ('x86_64', 'arm64x'):
            cached['architecture'] = architecture
            self.make_case('W1')
            with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'):
                self.check()

    def test_editor_and_project_modules_keep_the_declared_arm64_build_architecture(self):
        for role in ('editor', 'module'):
            images = self.build['external_inputs']['loaded_images']
            path = self.build['editor']['realpath'] if role == 'editor' else self.build['modules'][0]['realpath']
            image = next(row for row in images if row['realpath'] == path)
            image['architecture'] = 'arm64e'
            if role == 'module': self.build['modules'][0]['architecture'] = 'arm64e'
            self.make_case('W1')
            with self.assertRaisesRegex(ValueError, '^lcer.release_evidence_invalid$'):
                self.check()
            image['architecture'] = 'arm64'

    def test_build_execution_identity_and_missing_outer_inputs_reject(self):
        case, trace = self.records()
        for defect in ('missing_build', 'failed', 'argv', 'cwd', 'editor', 'project_size', 'missing_module', 'duplicate_images'):
            build = copy.deepcopy(self.build)
            if defect == 'missing_build': build = {}
            elif defect == 'failed': build['returncode'] = 1
            elif defect == 'argv': build['argv'].append('-Undeclared')
            elif defect == 'cwd': build['cwd'] += '/changed'
            elif defect == 'editor': build['editor']['sha256'] = 'f' * 64
            elif defect == 'project_size': build['project']['size_bytes'] += 1
            elif defect == 'missing_module': build['modules'] = []
            else: build['external_inputs']['loaded_images'].append(copy.deepcopy(build['external_inputs']['loaded_images'][0]))
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.check(case, trace, build=build)
        with self.assertRaises(ValueError):
            self.verifier._case_launch_relations(self.policy, case, trace, None, None, self.parents)

    def test_repeated_wrong_config_or_plugin_hash_does_not_authenticate_source(self):
        for category in ('engine_configs', 'engine_plugins'):
            self.setUp()
            self.build['external_inputs'][category][0]['sha256'] = 'f' * 64
            self.make_case('W1')
            case, trace = self.records()  # Recomputed valid bindings repeat the false input.
            with self.subTest(category=category), self.assertRaises(ValueError): self.check(case, trace)

    def test_omitted_or_added_project_config_rejects_even_when_inventories_match(self):
        for defect in ('missing', 'extra'):
            self.setUp()
            rows = self.build['external_inputs']['engine_configs']
            if defect == 'missing': rows.pop()
            else:
                rows.append(dict(rows[0], realpath=str(self.base / 'CityMaterializationProof/Config/Injected.ini')))
                rows.sort(key=lambda row: row['realpath'])
            self.make_case('W1')
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.check()

    def test_reused_or_nested_root_and_changed_parent_or_user_reject(self):
        for defect in ('reused', 'nested', 'parent', 'user'):
            self.make_case('W1')
            process = self.processes[1]
            root = self.processes[0]['environment']['HOME'][:-5]
            if defect in ('reused', 'nested'): self.launch_tuple(process, root if defect == 'reused' else root + '/nested')
            elif defect == 'parent': process['ppid'] += 2
            else: self.launch_tuple(process, process['environment']['HOME'][:-5], 'changed_user')
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.check()

    def test_replacement_launch_is_checked_without_fabricating_a_bind(self):
        for defect in ('argv', 'environment', 'image', 'world', 'root'):
            self.make_case('F07')
            process = self.processes[2]
            if defect == 'argv': process['argv'].append('-Injected')
            elif defect == 'environment': process['environment']['LCER_OWNER'] = 'domain_B'
            elif defect == 'image': process['loaded_images'][0]['sha256'] = 'f' * 64
            elif defect == 'world': process['startup']['worlds'][0]['game_mode_class'] = '/Script/Engine.GameMode'
            else: self.launch_tuple(process, self.processes[0]['environment']['HOME'][:-5])
            case, trace = self.records()
            self.assertEqual(len(case['process_bindings']), 2)
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.check(case, trace)

    def test_original_binding_and_raw_startup_are_not_replaceable_by_build_agreement(self):
        for defect in ('binding', 'startup', 'missing_startup', 'duplicate_startup'):
            case, trace = self.records()
            if defect == 'binding': case['process_bindings'][0]['input_inventory_sha256'] = 'f' * 64
            elif defect == 'startup':
                message = json.loads(trace['events'][0]['payload']['raw_line_utf8'])
                message['pid'] += 100
                trace['events'][0]['payload']['raw_line_utf8'] = stored_json_bytes(message).decode()
            elif defect == 'missing_startup': trace['events'].pop(0)
            else: trace['events'].insert(0, copy.deepcopy(trace['events'][0]))
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.check(case, trace)

    def test_consistent_module_name_without_native_mac_prefix_rejects(self):
        self.build = json.loads(json.dumps(self.build).replace('libUnrealEditor-CityLiveEvidenceProof.dylib',
            'UnrealEditor-CityLiveEvidenceProof.dylib'))
        self.make_case('W1')
        case, trace = self.records()
        with self.assertRaises(ValueError): self.check(case, trace)


class LivenessSeriesRelationTests(unittest.TestCase):
    """Supplied records exercise relations; these fixtures are not live proof."""

    def setUp(self):
        fixture = ProcessBindingRelationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.verifier, self.policy = fixture.verifier, fixture.policy
        process = copy.deepcopy(fixture.observation)
        child, parent = process['pid'], process['ppid']
        parent_pipes = []
        for number, row in enumerate(process['descriptors']):
            row.update(kernel_id='%016x' % (number * 2 + 1), peer_kernel_id='%016x' % (number * 2 + 2))
            parent_pipes.append(dict(row, pid=parent, fd=number + 10, kernel_id=row['peer_kernel_id'],
                                     peer_kernel_id=row['kernel_id'], access='write' if number == 0 else 'read'))
        pipes = sorted(parent_pipes + process['descriptors'], key=lambda row: (row['pid'], row['fd']))
        first = {'checkpoint': 'startup', 'domain': 'domain_A', 'launch_id': 'offline_launch',
                 'poll_returncode': None, 'observed_process': process,
                 'pipe_endpoints': copy.deepcopy(pipes), 'pipe_holders': copy.deepcopy(pipes)}
        self.samples = [first, copy.deepcopy(first), copy.deepcopy(first)]
        self.samples[1]['checkpoint'] = 'L0'
        self.samples[2].update(checkpoint='cleanup', poll_returncode=0, observed_process=None,
                              pipe_endpoints=[dict(row, peer_kernel_id=None) for row in parent_pipes],
                              pipe_holders=[dict(row, peer_kernel_id=None) for row in parent_pipes])

    def verify(self, samples=None):
        return self.verifier._liveness_series_relations(self.policy, self.samples if samples is None else samples)

    def test_live_to_exited_pipe_inventory_and_defensive_copy(self):
        result = self.verify()
        self.assertEqual(result, self.samples)
        result[0]['observed_process']['pid'] += 1
        self.assertNotEqual(result, self.samples)

    def test_dynamic_engine_descriptors_and_open_file_bytes_may_change(self):
        row = self.samples[1]['observed_process']
        row['descriptors'].append({'pid': row['pid'], 'fd': 8, 'kind': 'vnode', 'kernel_id': 'dynamic-vnode',
                                   'peer_kernel_id': None, 'access': 'read', 'path': '/fixture/dynamic.bin'})
        row['open_files'].append({'realpath': '/fixture/dynamic.bin', 'sha256': 'e' * 64, 'size_bytes': 17})
        self.assertEqual(self.verify(), self.samples)
        row['open_files'][0].update(sha256='f' * 64, size_bytes=19)
        self.verify()

    def test_each_original_process_identity_field_is_fixed(self):
        for field in ('pid', 'ppid', 'macos_birth_tuple', 'cwd_realpath', 'executable', 'argv',
                      'environment', 'loaded_images', 'startup'):
            changed = copy.deepcopy(self.samples)
            process = changed[1]['observed_process']
            if field in ('pid', 'ppid'): process[field] += 1
            elif field == 'macos_birth_tuple': process[field]['seconds'] += 1
            elif field == 'cwd_realpath': process[field] += '/changed'
            elif field == 'executable': process[field]['sha256'] = 'f' * 64
            elif field == 'argv': process[field].append('-Changed')
            elif field == 'environment': process[field]['USER'] = 'changed'
            elif field == 'loaded_images': process[field][0]['sha256'] = 'f' * 64
            else: process[field]['pid'] += 1
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, '^lcer.original_process_identity_mismatch$'):
                self.verify(changed)

    def test_extra_missing_duplicated_or_changed_holders_reject(self):
        for change in ('extra', 'missing', 'duplicate', 'access', 'kernel', 'peer'):
            changed = copy.deepcopy(self.samples)
            rows = changed[1]['pipe_holders']
            if change == 'extra': rows.append(dict(rows[0], fd=99))
            elif change == 'missing': rows.pop()
            elif change == 'duplicate': rows.append(copy.deepcopy(rows[0]))
            elif change == 'access': rows[0]['access'] = 'read_write'
            elif change == 'kernel': rows[0]['kernel_id'] = 'f' * 16
            else: rows[0]['peer_kernel_id'] = None
            code = 'lcer.proof_pipe_extra_holder' if change == 'extra' else 'lcer.original_pipe_identity_mismatch'
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^' + code + '$'):
                self.verify(changed)

    def test_consistently_replaced_endpoints_or_extra_child_descriptor_reject(self):
        changed = copy.deepcopy(self.samples)
        for field in ('pipe_endpoints', 'pipe_holders'):
            changed[1][field][0]['kernel_id'] = 'f' * 16
        with self.assertRaisesRegex(ValueError, '^lcer.original_pipe_identity_mismatch$'):
            self.verify(changed)
        changed = copy.deepcopy(self.samples)
        descriptors = changed[1]['observed_process']['descriptors']
        descriptors.append(dict(descriptors[0], fd=17))
        with self.assertRaisesRegex(ValueError, '^lcer.proof_pipe_extra_holder$'):
            self.verify(changed)

    def test_invalid_initial_pair_topology_is_not_a_trusted_baseline(self):
        for change in ('wrong_parent', 'wrong_access', 'one_way_peer', 'duplicate_kernel', 'short_kernel', 'zero_kernel', 'nonpipe'):
            changed = copy.deepcopy(self.samples)
            endpoints = changed[0]['pipe_endpoints']
            if change == 'wrong_parent': endpoints[0]['pid'] += 4
            elif change == 'wrong_access': endpoints[0]['access'] = 'read_write'
            elif change == 'one_way_peer': endpoints[0]['peer_kernel_id'] = 'f' * 16
            elif change == 'duplicate_kernel': endpoints[0]['kernel_id'] = endpoints[1]['kernel_id']
            elif change == 'short_kernel': endpoints[0]['kernel_id'] = 'abc'
            elif change == 'zero_kernel': endpoints[0]['kernel_id'] = '0' * 16
            else: endpoints[0]['kind'] = 'socket'
            changed[0]['pipe_holders'] = copy.deepcopy(endpoints)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^lcer.original_pipe_identity_mismatch$'):
                self.verify(changed)

    def test_poll_observation_and_post_exit_relations_cannot_fabricate_death_or_revival(self):
        for change in ('null_live', 'observed_dead', 'retained_child', 'retained_peer', 'changed_exit', 'revival'):
            changed = copy.deepcopy(self.samples)
            if change == 'null_live': changed[1]['observed_process'] = None
            elif change == 'observed_dead': changed[2]['observed_process'] = copy.deepcopy(changed[0]['observed_process'])
            elif change == 'retained_child':
                changed[2]['pipe_endpoints'] = copy.deepcopy(changed[0]['pipe_endpoints'])
                changed[2]['pipe_holders'] = copy.deepcopy(changed[0]['pipe_holders'])
            elif change == 'retained_peer':
                changed[2]['pipe_endpoints'][0]['peer_kernel_id'] = '1' * 16
                changed[2]['pipe_holders'] = copy.deepcopy(changed[2]['pipe_endpoints'])
            else:
                terminal = copy.deepcopy(changed[2]); terminal['checkpoint'] = 'terminal'
                changed.insert(2, terminal)
                if change == 'changed_exit': changed[-1]['poll_returncode'] = -15
                else: changed[-1] = dict(copy.deepcopy(changed[1]), checkpoint='cleanup')
            code = ('lcer.liveness_invalid' if change in ('null_live', 'observed_dead') else
                    'lcer.original_pipe_identity_mismatch' if change in ('retained_child', 'retained_peer') else
                    'lcer.original_process_identity_mismatch')
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^' + code + '$'):
                self.verify(changed)

    def test_duplicate_backward_and_post_cleanup_samples_reject(self):
        for checkpoints in (('startup', 'startup', 'cleanup'), ('startup', 'L2', 'L1'),
                            ('startup', 'cleanup', 'terminal')):
            changed = copy.deepcopy(self.samples)
            for row, checkpoint in zip(changed, checkpoints): row['checkpoint'] = checkpoint
            with self.subTest(checkpoints=checkpoints), self.assertRaisesRegex(ValueError, '^lcer.liveness_sequence_invalid$'):
                self.verify(changed)

    def test_descriptor_and_open_file_inventories_are_derived_from_rows(self):
        for change in ('duplicate_fd', 'missing_stdin', 'foreign_pid', 'missing_file', 'extra_file'):
            changed = copy.deepcopy(self.samples)
            process = changed[1]['observed_process']
            descriptors = process['descriptors']
            if change == 'duplicate_fd': descriptors.append(copy.deepcopy(descriptors[0]))
            elif change == 'missing_stdin': descriptors.pop(0)
            elif change == 'foreign_pid': descriptors[0]['pid'] += 1
            elif change == 'missing_file':
                descriptors.append(dict(descriptors[0], fd=8, kind='vnode', path='/fixture/missing'))
            else: process['open_files'].append({'realpath': '/fixture/extra', 'sha256': 'f' * 64, 'size_bytes': 1})
            code = 'lcer.original_pipe_identity_mismatch' if change == 'missing_stdin' else 'lcer.process_observation_invalid'
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^' + code + '$'):
                self.verify(changed)


class LivenessTraceRelationTests(unittest.TestCase):
    """Typed trace fixtures test the join, not authenticated live acquisition."""

    def setUp(self):
        fixture = LivenessSeriesRelationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.verifier, self.policy = fixture.verifier, fixture.policy
        self.prototype = fixture.samples[0]
        self.make_case('W1')

    def add(self, kind, payload, domain, operation=None):
        previous = self.events[-1] if self.events else None
        self.events.append({'sequence': len(self.events), 'event_id': kind, 'payload': copy.deepcopy(payload),
                            'domain': domain, 'operation_id': operation, 'monotonic_ns': len(self.events),
                            'previous_event_sha256': None if previous is None else hashlib.sha256(stored_json_bytes(previous)).hexdigest()})

    def wire(self, kind, payload):
        self.add('wire_event', {'direction': 'stdin' if kind == 'command' else 'stdout',
                               'parsed_schema': kind, 'raw_line_utf8': stored_json_bytes(payload).decode(),
                               'stream_byte_offset': 0}, payload['domain'], payload.get('operation_id'))

    def sample(self, index, checkpoint, dead=False):
        row = copy.deepcopy(self.templates[index])
        row['checkpoint'] = checkpoint
        if dead:
            parent = row['observed_process']['ppid']
            row.update(poll_returncode=-15, observed_process=None)
            row['pipe_endpoints'] = [dict(item, peer_kernel_id=None) for item in row['pipe_endpoints'] if item['pid'] == parent]
            row['pipe_holders'] = copy.deepcopy(row['pipe_endpoints'])
        if row['observed_process'] is not None:
            self.add('process_observation', row['observed_process'], row['domain'])
        self.add('liveness', row, row['domain'])

    def make_case(self, name):
        self.events = []; self.templates = []; bindings = []
        for index in range(3 if name == 'F07' else 2):
            domain = 'domain_B' if index == 1 else 'domain_A'
            row = copy.deepcopy(self.prototype)
            row.update(domain=domain, launch_id='offline_launch_%d' % index)
            process = row['observed_process']
            original_pid = process['pid']; process['pid'] += index
            process['startup'].update(witness_id=name, domain=domain, launch_id=row['launch_id'], pid=process['pid'])
            for field in ('pipe_endpoints', 'pipe_holders', 'descriptors'):
                rows = process[field] if field == 'descriptors' else row[field]
                for item in rows:
                    if item['pid'] == original_pid: item['pid'] = process['pid']
                    else: item['fd'] += index * 10
                    item['kernel_id'] = '%016x' % (int(item['kernel_id'], 16) + index * 100)
                    item['peer_kernel_id'] = '%016x' % (int(item['peer_kernel_id'], 16) + index * 100)
            self.templates.append(row)
            if index < 2:
                binding = schema_example(self.policy['wire_schemas']['process_binding'], self.policy['wire_schemas'])
                binding.update(witness_id=name, domain=domain, launch_id=row['launch_id'], pid=process['pid'],
                               macos_birth_tuple=copy.deepcopy(process['macos_birth_tuple']),
                               startup_sha256=hashlib.sha256(stored_json_bytes(process['startup'])).hexdigest(),
                               descriptor_map_sha256=hashlib.sha256(stored_json_bytes(process['descriptors'])).hexdigest())
                bindings.append(binding)
        for row in self.templates[:2]: self.wire('startup', row['observed_process']['startup'])
        complete = ['startup', 'L0', 'L1', 'L2', 'before_resolve', 'after_resolve', 'L3', 'L4', 'L5']
        if name.startswith('W'): checkpoints = complete + ['cleanup']
        elif name.startswith('C'): checkpoints = complete[:6] + ['terminal', 'cleanup']
        else:
            end = (2 if name in ('F01', 'F08', 'F09') else
                   3 if name in ('F02', 'F03', 'F04a', 'F04b', 'F05', 'F06') else
                   4 if name == 'F07' else 7)
            checkpoints = complete[:end] + ['terminal', 'cleanup']
        dead_domain = {'F07': 'domain_A', 'F08': 'domain_B', 'F11': 'domain_A', 'F12': 'domain_B'}.get(name)
        for checkpoint in checkpoints:
            if name == 'F07' and checkpoint == 'terminal':
                self.wire('startup', self.templates[2]['observed_process']['startup'])
                program = next(row for row in self.policy['failure_programs'] if row['id'] == 'F07')
                before = dict(copy.deepcopy(self.templates[0]), checkpoint='terminal')
                after = dict(copy.deepcopy(self.templates[2]), checkpoint='terminal')
                payload = {key: program[key] for key in ('executor', 'stage', 'action', 'underlying_code')}
                payload.update(failure_case='F07', consumed=True, before={'kind': 'process', 'sample': before},
                               after={'kind': 'process', 'sample': after})
                self.add('fault_event', payload, 'domain_A')
            for index, domain in enumerate(('domain_A', 'domain_B')):
                self.sample(index, checkpoint, checkpoint == 'cleanup' or (checkpoint == 'terminal' and domain == dead_domain))
                if checkpoint == 'startup':
                    binding = bindings[index]
                    command = {'schema': 'city.live_evidence_command.v1', 'witness_id': name, 'domain': domain,
                               'launch_id': binding['launch_id'], 'operation_id': 'bind_0001', 'command': 'bind',
                               'binding_sha256': hashlib.sha256(stored_json_bytes(binding)).hexdigest(), 'payload': binding}
                    self.wire('command', command)
        if name == 'F07': self.sample(2, 'cleanup', True)
        self.case = {'witness_id': name, 'process_bindings': bindings, 'liveness_checkpoints': []}
        self.sync()

    def sync(self):
        previous = None
        for number, row in enumerate(self.events):
            row.update(sequence=number, monotonic_ns=number, previous_event_sha256=previous)
            previous = hashlib.sha256(stored_json_bytes(row)).hexdigest()
        self.case['liveness_checkpoints'] = [copy.deepcopy(row['payload']) for row in self.events if row['event_id'] == 'liveness']

    def verify(self):
        return self.verifier._liveness_trace_relations(self.policy, self.case, {'events': self.events})

    def test_every_frozen_case_has_exact_checkpoint_pairs_and_replacement_scope(self):
        names = ['W%d' % number for number in range(1, 9)]
        names += [row['id'] for row in self.policy['failure_programs']]
        names += ['C%02d' % number for number in range(1, 7)]
        self.assertEqual(len(names), 35)
        for name in names:
            self.make_case(name)
            with self.subTest(case=name):
                result = self.verify()
                self.assertEqual(len(result), 3 if name == 'F07' else 2)

    def test_missing_checkpoint_rejects_after_removing_both_repeated_copies(self):
        selected = next(i for i, row in enumerate(self.events) if row['event_id'] == 'liveness' and
                        row['payload']['checkpoint'] == 'L2' and row['domain'] == 'domain_A')
        del self.events[selected - 1:selected + 1]
        self.sync()
        with self.assertRaisesRegex(ValueError, '^lcer.liveness_sequence_invalid$'): self.verify()

    def test_missing_adjacent_process_observation_or_extra_record_rejects(self):
        for change in ('missing', 'orphan', 'changed'):
            self.make_case('W1')
            selected = next(i for i, row in enumerate(self.events) if row['event_id'] == 'process_observation')
            if change == 'missing': self.events.pop(selected)
            elif change == 'orphan': self.events.insert(selected, copy.deepcopy(self.events[selected]))
            else: self.events[selected]['payload']['pid'] += 1
            self.sync()
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^lcer.liveness_invalid$'): self.verify()

    def test_repeated_case_samples_cannot_diverge_from_trace(self):
        self.case['liveness_checkpoints'][0]['poll_returncode'] = 0
        with self.assertRaisesRegex(ValueError, '^lcer.liveness_invalid$'): self.verify()

    def test_binding_must_follow_its_initial_observation(self):
        selected = next(i for i, row in enumerate(self.events) if row['event_id'] == 'wire_event' and
                        row['payload']['parsed_schema'] == 'command')
        self.events.insert(2, self.events.pop(selected))
        self.sync()
        with self.assertRaisesRegex(ValueError, '^lcer.binding_mismatch$'): self.verify()

    def test_changed_binding_identity_rejects_even_with_matching_command_copy(self):
        binding = self.case['process_bindings'][0]
        binding['pid'] += 100
        event = next(row for row in self.events if row['event_id'] == 'wire_event' and row['domain'] == 'domain_A' and
                     row['payload']['parsed_schema'] == 'command')
        message = json.loads(event['payload']['raw_line_utf8'])
        message['payload'] = copy.deepcopy(binding)
        event['payload']['raw_line_utf8'] = stored_json_bytes(message).decode()
        self.sync()
        with self.assertRaisesRegex(ValueError, '^lcer.binding_mismatch$'): self.verify()

    def test_sampling_either_domain_first_within_a_later_pair_is_allowed(self):
        selected = next(i for i, row in enumerate(self.events) if row['event_id'] == 'liveness' and
                        row['payload']['checkpoint'] == 'L1' and row['domain'] == 'domain_A')
        start = selected - 1
        self.events[start:start + 4] = self.events[start + 2:start + 4] + self.events[start:start + 2]
        self.sync()
        self.verify()

    def test_interleaved_checkpoint_pairs_reject(self):
        selected = next(i for i, row in enumerate(self.events) if row['event_id'] == 'liveness' and
                        row['payload']['checkpoint'] == 'L1' and row['domain'] == 'domain_A')
        start = selected - 1
        self.events[start + 2:start + 6] = self.events[start + 4:start + 6] + self.events[start + 2:start + 4]
        self.sync()
        with self.assertRaisesRegex(ValueError, '^lcer.liveness_sequence_invalid$'): self.verify()

    def test_individually_valid_launches_cannot_share_parent_descriptors(self):
        for event in self.events:
            if event['event_id'] == 'liveness' and event['domain'] == 'domain_B':
                for field in ('pipe_endpoints', 'pipe_holders'):
                    for row in event['payload'][field]:
                        if row['pid'] == self.templates[1]['observed_process']['ppid']:
                            row['fd'] -= 10
        self.sync()
        rows = [row for row in self.case['liveness_checkpoints'] if row['domain'] == 'domain_B']
        self.verifier._liveness_series_relations(self.policy, rows)
        with self.assertRaisesRegex(ValueError, '^lcer.original_pipe_identity_mismatch$'): self.verify()

    def test_undeclared_terminal_death_rejects(self):
        self.make_case('F01')
        selected = next(i for i, row in enumerate(self.events) if row['event_id'] == 'liveness' and
                        row['payload']['checkpoint'] == 'terminal' and row['domain'] == 'domain_A')
        cleanup = next(row['payload'] for row in self.events if row['event_id'] == 'liveness' and
                       row['payload']['checkpoint'] == 'cleanup' and row['domain'] == 'domain_A')
        self.events[selected]['payload'] = dict(copy.deepcopy(cleanup), checkpoint='terminal')
        self.events.pop(selected - 1)
        self.sync()
        with self.assertRaisesRegex(ValueError, '^lcer.terminal_process_invalid$'): self.verify()

    def test_replacement_requires_its_fault_observation_and_exit(self):
        for change in ('missing_fault', 'wrong_launch', 'live_cleanup'):
            self.make_case('F07')
            selected = next(i for i, row in enumerate(self.events) if row['event_id'] == 'fault_event')
            if change == 'missing_fault': self.events.pop(selected)
            elif change == 'wrong_launch': self.events[selected]['payload']['after']['sample']['launch_id'] = 'foreign'
            else:
                self.events.pop()
                self.sample(2, 'cleanup', False)
            self.sync()
            code = 'lcer.terminal_process_invalid' if change == 'live_cleanup' else 'lcer.liveness_invalid'
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, '^' + code + '$'): self.verify()


class ProcessBindingRelationTests(unittest.TestCase):
    """Record fixtures test binding relations only, never acquisition reality."""

    def setUp(self):
        previous = list(sys.path)
        import verify_live_cross_domain_evidence_round_trip_release as verifier
        sys.path[:] = previous
        self.verifier = verifier
        self.contract_raw = CONTRACT_PATH.read_bytes()
        self.policy = json.loads(self.contract_raw)
        self.root = '/private/tmp/offline-binding/W1/domain_A'
        self.operator = 'offline_operator'
        base = '/Users/boandersson/Projects/CITY'
        image = {'realpath': base + '/' + self.policy['runtime']['plugin'] + '/Binaries/Mac/UnrealEditor-CityLiveEvidenceProof.dylib',
                 'sha256': 'a' * 64, 'macho_uuid': 'offline-module-uuid', 'architecture': 'arm64', 'source': 'dyld'}
        controller_path = '/Engine/Maps/Entry.Entry:PersistentLevel.Controller'
        actor = {'actor_id': '/Engine/Maps/Entry.Entry|' + controller_path, 'actor_path': controller_path,
                 'class_path': '/Script/Engine.PlayerController', 'world_path': '/Engine/Maps/Entry.Entry',
                 'role': None, 'domain': None, 'record_raw_sha256': None, 'generation': None,
                 'allocation_owner': None, 'pending_kill': False, 'auto_receive_input': 0}
        world = {'world_path': '/Engine/Maps/Entry.Entry', 'world_type': 'Game',
                 'game_mode_class': self.policy['runtime']['game_mode'], 'actor_array_size': 2,
                 'visited_slots': [0, 1], 'null_slots': [0], 'actors': [actor]}
        self.startup = {'schema': 'city.live_evidence_startup.v1', 'witness_id': 'W1', 'domain': 'domain_A',
                        'launch_id': 'offline_launch', 'pid': 12345, 'cwd_realpath': base, 'worlds': [world],
                        'controllers': [{'actor_path': controller_path, 'class_path': actor['class_path'], 'pawn_path': None}],
                        'loaded_images': [image], 'proof_module': image,
                        'enabled_plugins': [{'realpath': base + '/' + self.policy['runtime']['plugin'] + '/CityLiveEvidenceProof.uplugin',
                                             'sha256': 'b' * 64, 'size_bytes': 3}],
                        'config_files': [{'realpath': base + '/CityMaterializationProof/Config/DefaultEngine.ini',
                                          'sha256': 'c' * 64, 'size_bytes': 4}]}
        self.project = {'realpath': base + '/' + self.policy['runtime']['project'],
                        'sha256': self.policy['unchanged_dependencies'][self.policy['runtime']['project']], 'size_bytes': 5}
        values = dict(engine=self.policy['runtime']['engine'], absolute_city_project=self.project['realpath'],
                      absolute_domain_root=self.root, observed_operator_user=self.operator,
                      witness_id='W1', domain='domain_A', launch_id='offline_launch')
        self.observation = {'pid': 12345, 'ppid': 12344, 'macos_birth_tuple': {'seconds': 1700000000, 'microseconds': 300},
                            'cwd_realpath': base, 'executable': {'realpath': self.policy['runtime']['engine'],
                                                               'sha256': 'd' * 64, 'size_bytes': 6},
                            'argv': [value.format_map(values) for value in self.policy['launch_argv']],
                            'environment': {key: value.format_map(values) for key, value in self.policy['launch_environment'].items()},
                            'descriptors': [{'pid': 12345, 'fd': number, 'kind': 'pipe', 'kernel_id': 'child%d' % number,
                                             'peer_kernel_id': 'parent%d' % number, 'access': access, 'path': None}
                                            for number, access in enumerate(('read', 'write', 'write'))],
                            'open_files': [], 'loaded_images': copy.deepcopy(self.startup['loaded_images']),
                            'startup': copy.deepcopy(self.startup)}
        self.parents = {'/Script/CoreUObject.Object': None, '/Script/Engine.Actor': '/Script/CoreUObject.Object',
                        '/Script/Engine.Controller': '/Script/Engine.Actor',
                        '/Script/Engine.PlayerController': '/Script/Engine.Controller'}

    def construct(self):
        return process_binding_from_observation(self.contract_raw, stored_json_bytes(self.startup), self.observation,
                                                self.project, self.root, self.operator)

    def verify(self, binding):
        return self.verifier._binding_relations(self.policy, binding, stored_json_bytes(self.startup),
                                                self.observation, self.project, self.root, self.operator, self.parents)

    def test_exact_digests_and_independent_world_reconstruction(self):
        binding = self.construct()
        self.assertEqual(set(binding), set(self.policy['process_binding_fields']))
        inputs = {key: self.startup[key] for key in ('loaded_images', 'enabled_plugins', 'config_files', 'proof_module')}
        for key, value in [('argv', self.observation['argv']), ('environment', self.observation['environment']),
                           ('descriptor_map', self.observation['descriptors']), ('cwd', self.observation['cwd_realpath']),
                           ('module_inventory', self.observation['loaded_images']), ('input_inventory', inputs),
                           ('startup', self.startup)]:
            expected = (json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')) + '\n').encode('utf-8')
            self.assertEqual(binding[key + '_sha256'], hashlib.sha256(expected).hexdigest())
            self.assertNotEqual(binding[key + '_sha256'], hashlib.sha256(expected[:-1]).hexdigest())
        facts = self.verify(binding)
        self.assertEqual(len(facts['controllers']), 1)
        self.assertEqual(facts['relevant'], [])

    def test_every_binding_field_change_rejects(self):
        original = self.construct()
        for key in self.policy['process_binding_fields']:
            changed = copy.deepcopy(original)
            if key.endswith('_sha256'): changed[key] = 'f' * 64
            elif key == 'pid': changed[key] += 1
            elif key == 'macos_birth_tuple': changed[key]['microseconds'] += 1
            elif key == 'domain': changed[key] = 'domain_B'
            else: changed[key] += '_changed'
            with self.subTest(field=key), self.assertRaisesRegex(ValueError, '^lcer.binding_mismatch$'):
                self.verify(changed)

    def test_launch_changes_reject_before_new_hash_can_authorize_them(self):
        original = copy.deepcopy(self.observation)
        for kind in ('argv_order', 'argv_extra', 'wrong_root', 'extra_environment', 'wrong_user', 'cwd', 'executable'):
            self.observation = copy.deepcopy(original)
            if kind == 'argv_order': self.observation['argv'][4:6] = self.observation['argv'][4:6][::-1]
            if kind == 'argv_extra': self.observation['argv'].append('-Injected')
            if kind == 'wrong_root': self.observation['argv'][11] += '/peer'
            if kind == 'extra_environment': self.observation['environment']['LCER_OWNER'] = 'domain_B'
            if kind == 'wrong_user': self.observation['environment']['USER'] = 'other'
            if kind == 'cwd': self.observation['cwd_realpath'] += '/subdirectory'
            if kind == 'executable': self.observation['executable']['realpath'] += '-other'
            with self.subTest(kind=kind), self.assertRaises(ValueError): self.construct()
            with self.subTest(independent=kind), self.assertRaises(ValueError): self.verify(schema_example(
                self.policy['wire_schemas']['process_binding'], self.policy['wire_schemas']))

    def test_original_three_pipes_are_hashed_and_dynamic_descriptors_retained(self):
        binding = self.construct()
        self.observation['descriptors'].append({'pid': 12345, 'fd': 9, 'kind': 'kqueue', 'kernel_id': 'queue',
                                               'peer_kernel_id': None, 'access': 'read_write', 'path': None})
        self.assertEqual(self.construct(), binding)
        self.verify(binding)
        original = copy.deepcopy(self.observation['descriptors'])
        for defect in ('missing', 'duplicate_fd', 'wrong_pid', 'wrong_access', 'closed_peer', 'shared_endpoint', 'redirect'):
            self.observation['descriptors'] = copy.deepcopy(original)
            rows = self.observation['descriptors']
            if defect == 'missing': rows.pop(1)
            if defect == 'duplicate_fd': rows.append(copy.deepcopy(rows[0]))
            if defect == 'wrong_pid': rows[0]['pid'] += 1
            if defect == 'wrong_access': rows[0]['access'] = 'read_write'
            if defect == 'closed_peer': rows[0]['peer_kernel_id'] = None
            if defect == 'shared_endpoint': rows[0]['peer_kernel_id'] = rows[1]['kernel_id']
            if defect == 'redirect': rows[0].update(kind='vnode', path='/private/tmp/redirect')
            with self.subTest(defect=defect), self.assertRaisesRegex(ValueError, '^lcer.original_pipe_identity_mismatch$'):
                self.construct()
            with self.subTest(independent=defect), self.assertRaises(ValueError): self.verify(binding)

    def test_startup_and_current_process_cannot_be_mixed(self):
        binding = self.construct()
        original = copy.deepcopy(self.startup)
        for defect in ('pid', 'launch', 'image_hash', 'module', 'duplicate_inventory', 'relative_inventory'):
            self.startup = copy.deepcopy(original)
            if defect == 'pid': self.startup['pid'] += 1
            if defect == 'launch': self.startup['launch_id'] += '_replacement'
            if defect == 'image_hash': self.startup['loaded_images'][0]['sha256'] = 'e' * 64
            if defect == 'module': self.startup['proof_module'] = dict(self.startup['proof_module'], realpath='/unmapped')
            if defect == 'duplicate_inventory': self.startup['enabled_plugins'].append(copy.deepcopy(self.startup['enabled_plugins'][0]))
            if defect == 'relative_inventory': self.startup['config_files'][0]['realpath'] = 'relative.ini'
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.construct()
            with self.subTest(independent=defect), self.assertRaises(ValueError): self.verify(binding)
        # Even a consistently repeated inventory must obey its own identity rules.
        for field in ('loaded_images', 'enabled_plugins', 'config_files'):
            self.startup = copy.deepcopy(original); self.startup[field].append(copy.deepcopy(self.startup[field][0]))
            self.observation['startup'] = copy.deepcopy(self.startup)
            self.observation['loaded_images'] = copy.deepcopy(self.startup['loaded_images'])
            with self.subTest(repeated=field), self.assertRaises(ValueError): self.construct()

    def test_consistently_rehashed_wrong_world_and_unknown_class_still_reject(self):
        original = copy.deepcopy(self.startup)
        for defect in ('wrong_game_mode', 'input_enabled', 'possessed_pawn', 'missing_slot', 'unknown_ancestry'):
            self.startup = copy.deepcopy(original)
            if defect == 'wrong_game_mode': self.startup['worlds'][0]['game_mode_class'] = '/Script/Engine.GameModeBase'
            if defect == 'input_enabled': self.startup['worlds'][0]['actors'][0]['auto_receive_input'] = 1
            if defect == 'possessed_pawn': self.startup['controllers'][0]['pawn_path'] = '/UnexpectedPawn'
            if defect == 'missing_slot': self.startup['worlds'][0]['visited_slots'].pop()
            if defect == 'unknown_ancestry': self.parents.pop('/Script/Engine.PlayerController')
            self.observation['startup'] = copy.deepcopy(self.startup)
            binding = self.construct()
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.verify(binding)

    def test_results_do_not_alias_original_records(self):
        before = stored_json_bytes({'startup': self.startup, 'observation': self.observation, 'project': self.project})
        binding = self.construct()
        facts = self.verify(binding)
        binding['macos_birth_tuple']['seconds'] = 1
        facts['controllers'][0]['actor_path'] = 'modified detached result'
        self.assertEqual(stored_json_bytes({'startup': self.startup, 'observation': self.observation, 'project': self.project}), before)


def closure_process_arguments(pid):
    """Read actual kernel argv, without archiving the process environment."""
    observer = MacProcessObserver()
    before = observer.identity(pid)
    maximum = ctypes.c_int()
    size = ctypes.c_size_t(ctypes.sizeof(maximum))
    if observer._libc.sysctl((ctypes.c_int * 2)(1, 8), 2, ctypes.byref(maximum), ctypes.byref(size), None, 0):
        raise ValueError('lcer.closure_process_unobserved')
    if not 0 < maximum.value <= 16 * 1024 * 1024:
        raise ValueError('lcer.closure_process_unobserved')
    buffer = ctypes.create_string_buffer(maximum.value)
    size = ctypes.c_size_t(len(buffer))
    if observer._libc.sysctl((ctypes.c_int * 3)(1, 49, pid), 3, buffer, ctypes.byref(size), None, 0):
        raise ValueError('lcer.closure_process_unobserved')
    raw = buffer.raw[:size.value]
    if len(raw) < 5:
        raise ValueError('lcer.closure_process_unobserved')
    count = struct.unpack('=i', raw[:4])[0]
    end = raw.find(b'\0', 4)
    if not 0 < count < 65536 or end < 5:
        raise ValueError('lcer.closure_process_unobserved')
    position = end + 1
    while position < len(raw) and raw[position] == 0:
        position += 1
    arguments = []
    for _ in range(count):
        end = raw.find(b'\0', position)
        if end < 0:
            raise ValueError('lcer.closure_process_unobserved')
        arguments.append(os.fsdecode(raw[position:end]))
        position = end + 1
    if observer.identity(pid) != before:
        raise ValueError('lcer.closure_process_changed')
    return {'identity': before, 'argv': arguments}


def capture_closure_command(argv, cwd, environment, timeout_seconds=None,
                            stdout_limit=4 * 1024 * 1024, stderr_limit=1024 * 1024):
    """Drain an actual owned command. Failed/truncated capture never passes.

    Keep the direct child unreaped until pipe draining ends. Its process-group
    ID therefore cannot be recycled before an owned timeout/budget kill.
    This is command provenance, not proof of game-process cleanup or authority.
    """
    started = time.time()
    # The whole acquisition has no frozen wall-time estimate. Its individual
    # operations/cases retain their 60/900-second limits in the harness. Do not
    # turn the 900-second per-case limit into a smaller whole-matrix limit.
    deadline = None if timeout_seconds is None else time.monotonic() + timeout_seconds
    outputs = {'stdout': bytearray(), 'stderr': bytearray()}
    limits = {'stdout': stdout_limit, 'stderr': stderr_limit}
    truncated = {'stdout': False, 'stderr': False}
    process = None
    observed = None
    failure = None
    pipes = {}
    eof = set()
    killed = False

    def terminate_owned_group():
        nonlocal killed
        if process is not None and not killed:
            # Popen owns this still-unreaped direct child and its new session.
            try:
                if os.getpgid(process.pid) != process.pid:
                    raise ValueError('lcer.closure_command_group_changed')
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            killed = True

    try:
        process = subprocess.Popen(argv, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True, close_fds=True)
        pipes = {process.stdout.fileno(): ('stdout', process.stdout),
                 process.stderr.fileno(): ('stderr', process.stderr)}
        try:
            observed = closure_process_arguments(process.pid)
            if (observed['identity']['ppid'] != os.getpid()
                    or observed['argv'][1:] != list(argv)[1:]):
                raise ValueError('lcer.closure_command_process_mismatch')
        except (ValueError, OSError) as error:
            failure = str(error) if isinstance(error, ValueError) else 'lcer.closure_command_process_unobserved'
            terminate_owned_group()
            deadline = time.monotonic() + 5
        while pipes:
            remaining = 0.05 if deadline is None else deadline - time.monotonic()
            if remaining <= 0:
                if failure is not None:
                    break
                failure = 'lcer.closure_command_timeout'
                terminate_owned_group()
                deadline = time.monotonic() + 5
                continue
            ready, _, _ = select.select(list(pipes), [], [], min(remaining, 0.05))
            for fd in ready:
                name, stream = pipes[fd]
                chunk = os.read(fd, 65536)
                if not chunk:
                    eof.add(name)
                    stream.close()
                    del pipes[fd]
                    continue
                available = limits[name] - len(outputs[name])
                outputs[name].extend(chunk[:available])
                if len(chunk) > available:
                    truncated[name] = True
                    if failure is None:
                        failure = 'lcer.closure_command_output_budget'
                        terminate_owned_group()
                        deadline = time.monotonic() + 5
        try:
            process.wait(timeout=None if deadline is None else max(0.001, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            failure = failure or 'lcer.closure_command_timeout'
            terminate_owned_group()
            process.wait(timeout=5)
    except OSError:
        failure = failure or 'lcer.closure_command_spawn_or_io_failed'
    finally:
        for _, stream in pipes.values():
            stream.close()
        if process is not None and process.returncode is None:
            terminate_owned_group()
            process.wait(timeout=5)
    stdout, stderr = bytes(outputs['stdout']), bytes(outputs['stderr'])
    record = {'schema': 'city.live_evidence_closure_command_capture.v1',
              'argv': list(argv), 'cwd': str(cwd),
              'environment_sha256': hashlib.sha256(stored_json_bytes(environment)).hexdigest(),
              'started_epoch': started, 'finished_epoch': time.time(),
              'timeout_seconds': timeout_seconds, 'process': observed,
              'exit_code': None if process is None else process.returncode,
              'failure_code': failure, 'group_termination_requested': killed,
              'stdout_limit': stdout_limit, 'stderr_limit': stderr_limit,
              'truncated': truncated, 'eof': sorted(eof),
              'capture_complete': failure is None and eof == {'stdout', 'stderr'}}
    return record, stdout, stderr


class ClosureExecutionContext:
    """One append-only, process-bound execution context for the sealed cases.

    Context records are test-driver development evidence, never game truth.
    A failed or interrupted case consumes its slot. No restart, acquisition
    reuse, caller-selected context, or fallback directory is permitted.
    """
    CONTRACT = 'Synthesis/ContractClosure/city.live-evidence-implementation.v1.contract.json'
    CONTRACT_SHA = '2641e2a639bac9f429284e71506dedc2bce607be5e4f05c8bb0439d6809c8c1c'
    SEAL = 'Synthesis/ContractClosure/city.live-evidence-implementation.v1.seal.json'
    SEAL_SHA = '3964ce2858571a9202d29e27f5f9599974900c7f4d37c003a16e5dc39b8ea9f6'

    @staticmethod
    def directory(repository, executor):
        key = stored_json_bytes({'repository': str(Path(repository).resolve()),
                                 'executor': executor, 'uid': os.getuid()})
        return Path('/private/tmp') / ('city-lcer-closure-' + hashlib.sha256(key).hexdigest())

    def __init__(self, repository):
        self.repository = Path(repository).absolute()
        self.observer = MacProcessObserver()
        self.executor = closure_process_arguments(os.getppid())
        self.process = self.observer.identity(os.getpid())
        if self.process['ppid'] != self.executor['identity']['pid']:
            raise ValueError('lcer.closure_process_changed')
        raw = source_file_bytes(self.repository.parent, self.CONTRACT, self.CONTRACT_SHA)
        source_file_bytes(self.repository.parent, self.SEAL, self.SEAL_SHA)
        self.cases = json.loads(raw)['execution_cases']
        self.root = self.directory(self.repository, self.executor['identity'])
        self.source = self._source()
        self.manifest = {'schema': 'city.live_evidence_closure_context.v2',
                         'executor': self.executor, 'repository': str(self.repository),
                         'source': self.source, 'context_path': str(self.root),
                         'contract_sha256': self.CONTRACT_SHA, 'seal_sha256': self.SEAL_SHA}
        self.manifest_raw = stored_json_bytes(self.manifest)
        self.manifest_hash = hashlib.sha256(self.manifest_raw).hexdigest()
        self.active = None

    def acquisition_argv(self, directory):
        policy = FrozenObligationPlanCompiler(CONTRACT_PATH.read_bytes()).compile()['constitutional_policy']
        values = {'absolute_unique_temp_root': str(directory / 'runtime'),
                  'fresh_output_root': str(directory / 'output')}
        return [item.format(**values) for item in policy['planned_commands']['acquire']]

    def acquire(self):
        if self.active != 1 or self.cases[self.active]['id'] != 'acquire-live-release':
            raise ValueError('lcer.closure_case_order_invalid')
        self._live_source()
        case = self.root / 'case-0001'
        directory = case / 'command'
        directory.mkdir(mode=0o700)
        environment = dict(os.environ)
        argv = self.acquisition_argv(directory)
        start = {'schema': 'city.live_evidence_closure_command_start.v1',
                 'case_start_sha256': hashlib.sha256(self._read(case / 'started.json')).hexdigest(),
                 'context_sha256': self.manifest_hash, 'argv': argv, 'cwd': str(self.repository),
                 'environment_sha256': hashlib.sha256(stored_json_bytes(environment)).hexdigest()}
        self._write(directory / 'started.json', stored_json_bytes(start))
        capture, stdout, stderr = capture_closure_command(argv, self.repository, environment)
        self._write(directory / 'stdout', stdout)
        self._write(directory / 'stderr', stderr)
        result = {'schema': 'city.live_evidence_closure_command_result.v1',
                  'started_sha256': hashlib.sha256(self._read(directory / 'started.json')).hexdigest(),
                  'capture': capture, 'stdout_sha256': hashlib.sha256(stdout).hexdigest(),
                  'stderr_sha256': hashlib.sha256(stderr).hexdigest()}
        self._write(directory / 'result.json', stored_json_bytes(result))
        self._live_source()
        self._command_hash(1)
        return result

    def _command_hash(self, index):
        case = self.root / ('case-%04d' % index)
        if index != 1:
            if (case / 'command').exists():
                raise ValueError('lcer.closure_context_ambiguous')
            return None
        directory = case / 'command'
        self._directory(directory)
        names = {p.name for p in directory.iterdir()}
        if (not {'started.json', 'stdout', 'stderr', 'result.json'}.issubset(names)
                or names - {'started.json', 'stdout', 'stderr', 'result.json', 'runtime', 'output'}):
            raise ValueError('lcer.closure_command_capture_invalid')
        start = parse_stored_json(self._read(directory / 'started.json'))
        raw = self._read(directory / 'result.json')
        result = parse_stored_json(raw)
        capture = result['capture']
        case_start = parse_stored_json(self._read(case / 'started.json'))
        capture_fields = {'schema','argv','cwd','environment_sha256','started_epoch','finished_epoch',
                          'timeout_seconds','process','exit_code','failure_code','group_termination_requested',
                          'stdout_limit','stderr_limit','truncated','eof','capture_complete'}
        if (set(start) != {'schema','case_start_sha256','context_sha256','argv','cwd','environment_sha256'}
                or start['schema'] != 'city.live_evidence_closure_command_start.v1'
                or start['case_start_sha256'] != hashlib.sha256(self._read(case / 'started.json')).hexdigest()
                or start['context_sha256'] != self.manifest_hash
                or start['argv'] != self.acquisition_argv(directory) or start['cwd'] != str(self.repository)
                or set(result) != {'schema','started_sha256','capture','stdout_sha256','stderr_sha256'}
                or result['schema'] != 'city.live_evidence_closure_command_result.v1'
                or result['started_sha256'] != hashlib.sha256(self._read(directory / 'started.json')).hexdigest()
                or set(capture) != capture_fields
                or capture['schema'] != 'city.live_evidence_closure_command_capture.v1'
                or any(capture[key] != start[key] for key in ('argv','cwd','environment_sha256'))):
            raise ValueError('lcer.closure_command_capture_invalid')
        if (capture['stdout_limit'] != 4 * 1024 * 1024 or capture['stderr_limit'] != 1024 * 1024
                or capture['timeout_seconds'] is not None
                or set(capture['truncated']) != {'stdout', 'stderr'}
                or any(type(value) is not bool for value in capture['truncated'].values())
                or type(capture['capture_complete']) is not bool
                or capture['eof'] != sorted(set(capture['eof']))
                or set(capture['eof']) - {'stdout', 'stderr'}):
            raise ValueError('lcer.closure_command_capture_invalid')
        if capture['capture_complete'] and (capture['failure_code'] is not None
                or capture['eof'] != ['stderr', 'stdout'] or any(capture['truncated'].values())
                or capture['process'] is None or type(capture['exit_code']) is not int):
            raise ValueError('lcer.closure_command_capture_invalid')
        if capture['process'] is not None:
            if (capture['process']['identity']['ppid'] != case_start['process']['pid']
                    or capture['process']['argv'][1:] != start['argv'][1:]):
                raise ValueError('lcer.closure_command_capture_invalid')
        for stream in ('stdout', 'stderr'):
            if result[stream+'_sha256'] != hashlib.sha256(self._read(directory / stream)).hexdigest():
                raise ValueError('lcer.closure_command_capture_changed')
        # Output directories are pending acquisition evidence. This route does
        # not accept their contents or derive live/build counts from their names.
        for name in names & {'runtime', 'output'}:
            self._directory(directory / name)
        return hashlib.sha256(raw).hexdigest()

    def _source(self):
        source_file_bytes(self.repository.parent, self.CONTRACT, self.CONTRACT_SHA)
        source_file_bytes(self.repository.parent, self.SEAL, self.SEAL_SHA)
        retained = retained_closure_contract(self.repository)
        argv = ['/usr/bin/git', 'rev-parse', '--show-toplevel', 'HEAD', 'HEAD^{tree}']
        result = subprocess.run(argv, cwd=self.repository, capture_output=True, timeout=30,
                                env={'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C',
                                     'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
                                     'GIT_OPTIONAL_LOCKS': '0'})
        values = result.stdout.decode('utf-8').splitlines()
        if (result.returncode != 0 or len(values) != 3 or values[0] != str(self.repository)
                or any(len(v) != 40 or any(c not in '0123456789abcdef' for c in v) for v in values[1:])):
            raise ValueError('lcer.closure_source_git_invalid')
        inventory = inspect_project_sources(CONTRACT_PATH.read_bytes(), self.repository)
        return {'commit': values[1], 'tree': values[2], 'retained': retained,
                'inventory': inventory, 'git_argv': argv,
                'git_stdout_base64': base64.b64encode(result.stdout).decode('ascii')}

    def _live_source(self):
        if (self.observer.identity(os.getpid()) != self.process
                or os.getppid() != self.executor['identity']['pid']
                or closure_process_arguments(os.getppid()) != self.executor):
            raise ValueError('lcer.closure_process_changed')
        if self._source() != self.source:
            raise ValueError('lcer.closure_source_changed')

    def _directory(self, path):
        info = path.lstat()
        if (not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700
                or info.st_uid != os.getuid() or path.resolve() != path):
            raise ValueError('lcer.closure_context_path_invalid')

    def _read(self, path):
        self._directory(path.parent)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            before = os.fstat(fd)
            if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                    or before.st_uid != os.getuid() or stat.S_IMODE(before.st_mode) != 0o600
                    or before.st_size > 4 * 1024 * 1024):
                raise ValueError('lcer.closure_context_file_invalid')
            with os.fdopen(fd, 'rb', closefd=False) as stream:
                raw = stream.read(4 * 1024 * 1024 + 1)
            after = os.fstat(fd)
            def identity(info):
                return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
                        info.st_uid, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
            if identity(before) != identity(after) or identity(after) != identity(path.lstat()) or len(raw) != after.st_size:
                raise ValueError('lcer.closure_context_changed')
            return raw
        finally:
            os.close(fd)

    def _write(self, path, raw):
        self._directory(path.parent)
        if type(raw) is not bytes or len(raw) > 4 * 1024 * 1024:
            raise ValueError('lcer.closure_output_budget_exceeded')
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, 'wb', closefd=False) as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(fd)
        finally:
            os.close(fd)

    def _previous(self, count):
        previous = self.manifest_hash
        expected = {'context.json'} | {'case-%04d' % n for n in range(count)}
        if {p.name for p in self.root.iterdir()} != expected:
            raise ValueError('lcer.closure_context_ambiguous')
        for index in range(count):
            directory = self.root / ('case-%04d' % index)
            self._directory(directory)
            members = {'started.json', 'stdout', 'stderr', 'result.json'} | ({'command'} if index == 1 else set())
            if {p.name for p in directory.iterdir()} != members:
                raise ValueError('lcer.closure_context_incomplete')
            start = parse_stored_json(self._read(directory / 'started.json'))
            raw = self._read(directory / 'result.json')
            result = parse_stored_json(raw)
            if (set(start) != {'schema','case_id','index','context_sha256','previous_sha256','process','argv'}
                    or start['schema'] != 'city.live_evidence_closure_case_start.v1'
                    or start['case_id'] != self.cases[index]['id'] or start['index'] != index
                    or start['context_sha256'] != self.manifest_hash or start['previous_sha256'] != previous
                    or start['process']['ppid'] != self.executor['identity']['pid']
                    or set(result) != {'schema','started_sha256','exit_code','stdout_sha256','stderr_sha256','case_accepted','command_sha256'}
                    or result['schema'] != 'city.live_evidence_closure_case_result.v2'
                    or result['started_sha256'] != hashlib.sha256(self._read(directory / 'started.json')).hexdigest()):
                raise ValueError('lcer.closure_context_mismatch')
            if result['command_sha256'] != self._command_hash(index):
                raise ValueError('lcer.closure_command_capture_changed')
            stdout, stderr = self._read(directory / 'stdout'), self._read(directory / 'stderr')
            if (result['stdout_sha256'] != hashlib.sha256(stdout).hexdigest()
                    or result['stderr_sha256'] != hashlib.sha256(stderr).hexdigest()):
                raise ValueError('lcer.closure_context_changed')
            # Re-evaluate raw output. A stored acceptance boolean is not authority.
            if not self._accepted(self.cases[index], result['exit_code'], stdout):
                raise ValueError('lcer.closure_context_failed')
            if result['case_accepted'] is not True:
                raise ValueError('lcer.closure_context_mismatch')
            if index == 1:
                # A forged passing summary cannot stand in for the independent
                # acquisition/release checks still required at this boundary.
                raise ValueError('lcer.closure_acquisition_validation_incomplete')
            previous = hashlib.sha256(raw).hexdigest()
        return previous

    @staticmethod
    def _accepted(case, exit_code, stdout):
        try:
            payload = parse_stored_json(stdout)
            if type(exit_code) is not int or exit_code != case['expected_exit']:
                return False
            for assertion in case['json_assertions']:
                value = payload
                for part in assertion['pointer'].strip('/').split('/'):
                    part = part.replace('~1', '/').replace('~0', '~')
                    value = value[int(part)] if isinstance(value, list) else value[part]
                if stored_json_bytes(value) != stored_json_bytes(assertion['equals']):
                    return False
            return set(case['expected_failure_codes']).issubset(set(payload.get('failure_codes', [])))
        except (ValueError, KeyError, TypeError, IndexError):
            return False

    def begin(self, case_id):
        self._live_source()
        indices = [n for n, c in enumerate(self.cases) if c['id'] == case_id]
        if len(indices) != 1 or self.active is not None:
            raise ValueError('lcer.closure_case_order_invalid')
        index = indices[0]
        if index == 0:
            try:
                self.root.mkdir(mode=0o700)
            except FileExistsError as error:
                raise ValueError('lcer.closure_context_exists') from error
            self._write(self.root / 'context.json', self.manifest_raw)
        elif not self.root.exists():
            raise ValueError('lcer.closure_context_missing')
        self._directory(self.root)
        if self._read(self.root / 'context.json') != self.manifest_raw:
            raise ValueError('lcer.closure_context_mismatch')
        previous = self._previous(index)
        directory = self.root / ('case-%04d' % index)
        directory.mkdir(mode=0o700)
        start = {'schema': 'city.live_evidence_closure_case_start.v1', 'case_id': case_id,
                 'index': index, 'context_sha256': self.manifest_hash, 'previous_sha256': previous,
                 'process': self.process, 'argv': closure_process_arguments(os.getpid())['argv']}
        self._write(directory / 'started.json', stored_json_bytes(start))
        self.active = index
        self._live_source()

    def finish(self, exit_code, stdout, stderr_stream):
        if self.active is None:
            raise ValueError('lcer.closure_case_order_invalid')
        self._live_source()
        directory = self.root / ('case-%04d' % self.active)
        sys.stderr.flush()
        stderr_stream.flush()
        stderr_stream.seek(0)
        stderr = stderr_stream.read(1024 * 1024 + 1)
        if len(stderr) > 1024 * 1024:
            raise ValueError('lcer.closure_output_budget_exceeded')
        self._write(directory / 'stdout', stdout)
        self._write(directory / 'stderr', stderr)
        result = {'schema': 'city.live_evidence_closure_case_result.v2',
                  'started_sha256': hashlib.sha256(self._read(directory / 'started.json')).hexdigest(),
                  'exit_code': exit_code, 'stdout_sha256': hashlib.sha256(stdout).hexdigest(),
                  'stderr_sha256': hashlib.sha256(stderr).hexdigest(),
                  'case_accepted': self._accepted(self.cases[self.active], exit_code, stdout),
                  'command_sha256': self._command_hash(self.active)}
        self._write(directory / 'result.json', stored_json_bytes(result))
        self.active = None
        return result


def retained_closure_contract(repository):
    """Authenticate the first sealed offline case from actual retained bytes.

    This is contract retention, not source-audit or live-release acceptance.
    The freeze has its own forward-record identity outside the game release.
    """
    raw = source_file_bytes(repository, 'proof_kernel/live_cross_domain_evidence_round_trip_contract.json')
    policy = FrozenObligationPlanCompiler(raw).compile()['constitutional_policy']
    before = inspect_project_sources(raw, repository)
    freeze_raw = source_file_bytes(repository, 'PHASE_5_FREEZE.json',
                                  'a6415491efd6abd75f6b1d14c542c33d560c0705cb483ef75afda7c74cca8a79')
    freeze = json.loads(freeze_raw)
    # Read every bound reviewed document, not a summary flag about its validity.
    for name, expected in sorted(freeze['frozen_documents'].items()):
        source_file_bytes(repository, name, expected)
    for name, expected in sorted(freeze['independent_review']['members'].items()):
        source_file_bytes(repository, name, expected)
    dependencies = core_health(raw, repository)
    if inspect_project_sources(raw, repository) != before:
        raise ValueError('lcer.closure_source_changed')
    return {'contract_raw_sha256': hashlib.sha256(raw).hexdigest(),
            'section_count': len(policy), 'freeze_raw_sha256': hashlib.sha256(freeze_raw).hexdigest(),
            'retained_dependency_count': len(dependencies['files'])}


def closure_case_main(argv=None):
    """Dispatch the test-only closure surface without inventing missing cases."""
    parser = argparse.ArgumentParser(description='Run one frozen CITY closure case', allow_abbrev=False)
    parser.add_argument('--closure-case', required=True)
    parser.add_argument('--json', action='store_true', required=True)
    args = parser.parse_args(argv)
    payload = {'schema': 'city.live_evidence_closure_case.v2', 'case_id': args.closure_case,
               'status': 'fail', 'observed': {}, 'failure_codes': [],
               'source_audit_complete': False, 'live_acceptance': False}
    context = None
    recorded = None
    case_directory = None
    stderr_stream = tempfile.TemporaryFile(mode='w+b')
    original_stderr = os.dup(2)
    os.dup2(stderr_stream.fileno(), 2)
    try:
        try:
            context = ClosureExecutionContext(CONTRACT_PATH.parent.parent)
            if args.closure_case not in {case['id'] for case in context.cases}:
                raise ValueError('lcer.closure_case_not_implemented')
            context.begin(args.closure_case)
            if args.closure_case == 'retained-contract':
                payload['observed'] = retained_closure_contract(CONTRACT_PATH.parent.parent)
                payload['observed']['execution_context_sha256'] = context.manifest_hash
                payload['status'] = 'pass'
            elif args.closure_case == 'acquire-live-release':
                result = context.acquire()
                payload['observed'] = {'command_result_sha256': context._command_hash(1),
                                       'command_exit_code': result['capture']['exit_code'],
                                       'command_stdout_sha256': result['stdout_sha256'],
                                       'command_stderr_sha256': result['stderr_sha256']}
                if not result['capture']['capture_complete'] or result['capture']['exit_code'] != 0:
                    raise ValueError(result['capture']['failure_code'] or 'lcer.closure_command_failed')
                raise ValueError('lcer.closure_acquisition_validation_incomplete')
            else:
                raise ValueError('lcer.closure_case_not_implemented')
        except (ValueError, OSError, KeyError, TypeError) as error:
            payload['failure_codes'] = [str(error) if isinstance(error, ValueError)
                                        else 'lcer.closure_input_invalid']
        code = 0 if payload['status'] == 'pass' else 2
        raw = stored_json_bytes(payload)
        if context is not None and context.active is not None:
            try:
                case_directory = context.root / ('case-%04d' % context.active)
                recorded = context.finish(code, raw, stderr_stream)
            except (ValueError, OSError, KeyError, TypeError) as error:
                payload.update(status='fail', observed={}, failure_codes=[str(error) if isinstance(error, ValueError)
                                                                          else 'lcer.closure_input_invalid'])
                code, raw = 2, stored_json_bytes(payload)
    finally:
        sys.stderr.flush()
        os.dup2(original_stderr, 2)
        os.close(original_stderr)
    stderr_stream.seek(0)
    stderr = stderr_stream.read(1024 * 1024 + 1)
    stderr_stream.close()
    if recorded is not None and recorded['stderr_sha256'] != hashlib.sha256(stderr).hexdigest():
        context._write(case_directory / 'capture-invalid.json', stored_json_bytes({
            'schema': 'city.live_evidence_closure_capture_failure.v1',
            'failure_code': 'lcer.closure_capture_changed'}))
        payload.update(status='fail', observed={}, failure_codes=['lcer.closure_capture_changed'])
        code, raw = 2, stored_json_bytes(payload)
    sys.stderr.buffer.write(stderr)
    sys.stderr.buffer.flush()
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()
    return code


class ClosureCommandBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='city-closure-entry-', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'CITY'
        policy = json.loads(CONTRACT_PATH.read_bytes())
        freeze = json.loads((CONTRACT_PATH.parent.parent / 'PHASE_5_FREEZE.json').read_bytes())
        names = (set(policy['planned_source_paths']) | set(policy['predecessors'])
                 | set(policy['unchanged_dependencies']) | set(policy['canonical_records'])
                 | set(freeze['frozen_documents']) | set(freeze['independent_review']['members'])
                 | {'PHASE_5_FREEZE.json'})
        for name in names:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((CONTRACT_PATH.parent.parent / name).read_bytes())
        for name in (ClosureExecutionContext.CONTRACT, ClosureExecutionContext.SEAL):
            target = self.root.parent / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((CONTRACT_PATH.parent.parent.parent / name).read_bytes())
        for argv in (['init', '-q'], ['add', '.'],
                     ['-c', 'user.name=CITY Fixture', '-c', 'user.email=fixture@invalid',
                      '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture source']):
            result = subprocess.run(['/usr/bin/git', *argv], cwd=self.root, capture_output=True, timeout=15,
                                    env={'PATH':'/usr/bin:/bin','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'})
            self.assertEqual(result.returncode, 0, result.stderr)
        self.context_root = ClosureExecutionContext.directory(self.root, MacProcessObserver().identity(os.getpid()))
        self.addCleanup(self.remove_context)

    def remove_context(self):
        if self.context_root.is_symlink():
            self.context_root.unlink()
        elif self.context_root.exists():
            shutil.rmtree(self.context_root)

    def invoke(self, case='retained-contract', extra=()):
        return subprocess.run([sys.executable, '-B', 'proof_kernel/test_live_cross_domain_evidence_round_trip.py',
                               '--closure-case', case, '--json', *extra], cwd=self.root,
                              capture_output=True, timeout=15)

    def test_actual_cli_authenticates_frozen_contract_and_review(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['status'], 'pass')
        self.assertEqual(payload['observed']['contract_raw_sha256'], hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest())
        self.assertEqual(payload['observed']['section_count'], 43)
        self.assertFalse(payload['live_acceptance'])
        self.assertFalse(payload['source_audit_complete'])

    def test_changed_forward_freeze_rejects_even_when_spec_is_intact(self):
        path = self.root / 'PHASE_5_FREEZE.json'
        path.write_bytes(path.read_bytes() + b'\n')
        result = self.invoke()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['failure_codes'], ['lcer.dependency_identity_mismatch'])

    def test_changed_preserved_review_cannot_supply_acceptance(self):
        path = self.root / 'References/Phase5SpecificationReview/draft3/REVIEW.md'
        path.write_bytes(path.read_bytes() + b'\n')
        result = self.invoke()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['failure_codes'], ['lcer.dependency_identity_mismatch'])

    def test_unimplemented_positive_negative_and_unknown_cases_never_pass(self):
        before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob('*'))
        for case in ('acquire-live-release', 'changed-schema', '../unknown'):
            with self.subTest(case=case):
                result = self.invoke(case)
                self.assertEqual(result.returncode, 2)
                payload = json.loads(result.stdout)
                self.assertEqual(payload['status'], 'fail')
                self.assertEqual(payload['observed'], {})
                expected = 'lcer.closure_case_not_implemented' if case == '../unknown' else 'lcer.closure_context_missing'
                self.assertEqual(payload['failure_codes'], [expected])
        self.assertEqual(sorted(str(path.relative_to(self.root)) for path in self.root.rglob('*')), before)

    def test_extra_cli_arguments_reject(self):
        result = self.invoke(extra=('--runtime-parent', str(self.root / 'unexpected')))
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / 'unexpected').exists())


class ClosureExecutionContextTests(unittest.TestCase):
    setUp = ClosureCommandBoundaryTests.setUp
    remove_context = ClosureCommandBoundaryTests.remove_context
    invoke = ClosureCommandBoundaryTests.invoke

    def first(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def rejected(self, result, code):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['status'], 'fail')
        self.assertEqual(payload['failure_codes'], [code])
        self.assertFalse(payload['live_acceptance'])

    def context_bytes(self):
        return {str(p.relative_to(self.context_root)): p.read_bytes()
                for p in self.context_root.rglob('*') if p.is_file()}

    def test_actual_parent_birth_argv_source_and_raw_result_are_bound(self):
        result = self.first()
        manifest_raw = (self.context_root / 'context.json').read_bytes()
        manifest = parse_stored_json(manifest_raw)
        self.assertEqual(manifest['executor'], closure_process_arguments(os.getpid()))
        identity = subprocess.check_output(['/usr/bin/git', 'rev-parse', 'HEAD', 'HEAD^{tree}'], cwd=self.root).decode().splitlines()
        self.assertEqual([manifest['source']['commit'], manifest['source']['tree']], identity)
        self.assertEqual(json.loads(result.stdout)['observed']['execution_context_sha256'], hashlib.sha256(manifest_raw).hexdigest())
        case = self.context_root / 'case-0000'
        start = parse_stored_json((case / 'started.json').read_bytes())
        self.assertEqual(start['process']['ppid'], os.getpid())
        self.assertEqual(start['argv'][-3:], ['--closure-case', 'retained-contract', '--json'])
        self.assertEqual((case / 'stdout').read_bytes(), result.stdout)
        self.assertEqual((case / 'stderr').read_bytes(), result.stderr)
        record = parse_stored_json((case / 'result.json').read_bytes())
        self.assertTrue(record['case_accepted'])
        self.assertEqual(record['stdout_sha256'], hashlib.sha256(result.stdout).hexdigest())
        self.assertEqual(record['stderr_sha256'], hashlib.sha256(result.stderr).hexdigest())

    def test_following_case_uses_same_context_and_retains_its_real_failure(self):
        self.first()
        result = self.invoke('acquire-live-release')
        self.rejected(result, 'lcer.closure_command_failed')
        case = self.context_root / 'case-0001'
        self.assertEqual((case / 'stdout').read_bytes(), result.stdout)
        self.assertEqual((case / 'stderr').read_bytes(), result.stderr)
        self.assertFalse(parse_stored_json((case / 'result.json').read_bytes())['case_accepted'])
        self.rejected(self.invoke('verify-live-release'), 'lcer.closure_context_failed')
        self.assertFalse((self.context_root / 'case-0002').exists())

    def test_actual_dispatch_diagnostics_are_captured_instead_of_assumed_empty(self):
        path = self.root / 'proof_kernel/test_live_cross_domain_evidence_round_trip.py'
        text = path.read_text()
        marker = "\n    raw = source_file_bytes(repository, 'proof_kernel/live_cross_domain_evidence_round_trip_contract.json')"
        self.assertEqual(text.count(marker), 1)
        path.write_text(text.replace(marker, "\n    print('actual closure diagnostic', file=sys.stderr)" + marker))
        result = self.first()
        self.assertIn(b'actual closure diagnostic\n', result.stderr)
        self.assertEqual((self.context_root / 'case-0000/stderr').read_bytes(), result.stderr)

    def test_repeated_first_case_cannot_reuse_or_overwrite_an_execution(self):
        self.first()
        before = self.context_bytes()
        self.rejected(self.invoke(), 'lcer.closure_context_exists')
        self.assertEqual(self.context_bytes(), before)

    def test_changed_worktree_bytes_reject_even_when_commit_is_unchanged(self):
        self.first()
        path = self.root / 'proof_kernel/test_live_cross_domain_evidence_round_trip.py'
        path.write_bytes(path.read_bytes() + b'\n# changed candidate\n')
        self.rejected(self.invoke('acquire-live-release'), 'lcer.closure_context_mismatch')
        self.assertFalse((self.context_root / 'case-0001').exists())

    def test_new_commit_cannot_reuse_old_source_context(self):
        self.first()
        result = subprocess.run(['/usr/bin/git', '-c', 'user.name=CITY Fixture', '-c', 'user.email=fixture@invalid',
                                 '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false',
                                 'commit', '--allow-empty', '-qm', 'new source identity'], cwd=self.root, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.rejected(self.invoke('acquire-live-release'), 'lcer.closure_context_mismatch')

    def test_extra_context_member_is_ambiguous_not_silently_ignored(self):
        self.first()
        (self.context_root / 'unexpected').write_bytes(b'other execution')
        self.rejected(self.invoke('acquire-live-release'), 'lcer.closure_context_ambiguous')

    def test_interrupted_case_cannot_be_recovered_as_a_completed_case(self):
        self.first()
        (self.context_root / 'case-0000/result.json').unlink()
        self.rejected(self.invoke('acquire-live-release'), 'lcer.closure_context_incomplete')
        self.assertFalse((self.context_root / 'case-0001').exists())

    def test_rehashed_bad_output_cannot_borrow_a_stored_acceptance_boolean(self):
        self.first()
        case = self.context_root / 'case-0000'
        payload = parse_stored_json((case / 'stdout').read_bytes())
        payload['observed']['section_count'] = 42
        raw = stored_json_bytes(payload)
        (case / 'stdout').write_bytes(raw)
        result = parse_stored_json((case / 'result.json').read_bytes())
        result['stdout_sha256'] = hashlib.sha256(raw).hexdigest()
        self.assertTrue(result['case_accepted'])
        (case / 'result.json').write_bytes(stored_json_bytes(result))
        self.rejected(self.invoke('acquire-live-release'), 'lcer.closure_context_failed')

    def test_different_actual_executor_cannot_find_or_reuse_the_context(self):
        self.first()
        before = self.context_bytes()
        program = ('import subprocess,sys; r=subprocess.run([sys.executable,"-B",'
                   '"proof_kernel/test_live_cross_domain_evidence_round_trip.py",'
                   '"--closure-case","acquire-live-release","--json"],capture_output=True);'
                   'sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);sys.exit(r.returncode)')
        result = subprocess.run([sys.executable, '-B', '-c', program], cwd=self.root, capture_output=True, timeout=15)
        self.rejected(result, 'lcer.closure_context_missing')
        self.assertEqual(self.context_bytes(), before)

    def test_archived_output_cannot_be_a_symlink_or_hardlink(self):
        self.first()
        path = self.context_root / 'case-0000/stdout'
        original = path.read_bytes()
        other = self.root.parent / 'other-output'
        other.write_bytes(original)
        other.chmod(0o600)
        path.unlink()
        path.symlink_to(other)
        self.rejected(self.invoke('acquire-live-release'), 'lcer.closure_input_invalid')
        path.unlink()
        os.link(other, path)
        self.rejected(self.invoke('acquire-live-release'), 'lcer.closure_context_file_invalid')

    def test_changed_root_seal_rejects_before_context_creation(self):
        path = self.root.parent / ClosureExecutionContext.SEAL
        path.write_bytes(path.read_bytes() + b'\n')
        self.rejected(self.invoke(), 'lcer.dependency_identity_mismatch')
        self.assertFalse(self.context_root.exists())

    def test_pid_only_manifest_cannot_drop_the_actual_birth_identity(self):
        self.first()
        path = self.context_root / 'context.json'
        value = parse_stored_json(path.read_bytes())
        value['executor']['identity']['macos_birth_tuple']['microseconds'] += 1
        path.write_bytes(stored_json_bytes(value))
        self.rejected(self.invoke('acquire-live-release'), 'lcer.closure_context_mismatch')


class ClosureCommandCaptureTests(unittest.TestCase):
    """Actual local children prove capture mechanics, never live Unreal work."""
    def run_program(self, program, **limits):
        with tempfile.TemporaryDirectory(prefix='city-command-capture-', dir='/private/tmp') as temporary:
            argv = [sys.executable, '-I', '-B', '-c', program]
            result = capture_closure_command(argv, Path(temporary), dict(os.environ), **limits)
        capture = result[0]
        if capture['process'] is not None:
            with self.assertRaises(ChildProcessError):
                os.waitpid(capture['process']['identity']['pid'], os.WNOHANG)
        return result

    def test_both_raw_streams_are_drained_and_nonzero_exit_is_preserved(self):
        program = "import os,time;os.write(1,b'\\x00\\xffA'*100000);os.write(2,b'\\xfeB'*100000);time.sleep(.1);raise SystemExit(7)"
        capture, stdout, stderr = self.run_program(program, timeout_seconds=10)
        self.assertEqual(stdout, b'\x00\xffA' * 100000)
        self.assertEqual(stderr, b'\xfeB' * 100000)
        self.assertEqual(capture['exit_code'], 7)
        self.assertTrue(capture['capture_complete'])
        self.assertIsNone(capture['failure_code'])
        self.assertEqual(capture['process']['identity']['ppid'], os.getpid())
        self.assertEqual(capture['process']['argv'][1:], capture['argv'][1:])

    def test_stdout_budget_retains_only_actual_prefix_and_reaps_producer(self):
        capture, stdout, stderr = self.run_program(
            "import os,time;os.write(1,b'A'*131072);time.sleep(30)", timeout_seconds=10, stdout_limit=64)
        self.assertEqual(stdout, b'A'*64)
        self.assertEqual(capture['failure_code'], 'lcer.closure_command_output_budget')
        self.assertTrue(capture['truncated']['stdout'])
        self.assertFalse(capture['capture_complete'])
        self.assertTrue(capture['group_termination_requested'])
        self.assertLess(capture['exit_code'], 0)

    def test_stderr_budget_is_independent_of_stdout_budget(self):
        capture, stdout, stderr = self.run_program(
            "import os,time;os.write(1,b'ok');os.write(2,b'E'*131072);time.sleep(30)",
            timeout_seconds=10, stderr_limit=32)
        self.assertEqual(stdout, b'ok')
        self.assertEqual(stderr, b'E'*32)
        self.assertEqual(capture['failure_code'], 'lcer.closure_command_output_budget')
        self.assertTrue(capture['truncated']['stderr'])
        self.assertFalse(capture['truncated']['stdout'])

    def test_explicit_fixture_timeout_cannot_report_a_successful_capture(self):
        capture, stdout, stderr = self.run_program(
            "import os,time;os.write(1,b'waiting');time.sleep(30)", timeout_seconds=0.4)
        self.assertEqual(capture['failure_code'], 'lcer.closure_command_timeout')
        self.assertFalse(capture['capture_complete'])
        self.assertTrue(capture['group_termination_requested'])
        self.assertLess(capture['exit_code'], 0)

    def test_spawn_failure_has_no_invented_process_or_exit(self):
        capture, stdout, stderr = capture_closure_command(
            ['/nonexistent/city-proof-command'], Path('/private/tmp'), dict(os.environ), timeout_seconds=1)
        self.assertEqual(capture['failure_code'], 'lcer.closure_command_spawn_or_io_failed')
        self.assertIsNone(capture['process'])
        self.assertIsNone(capture['exit_code'])
        self.assertEqual((stdout, stderr), (b'', b''))
        self.assertFalse(capture['capture_complete'])


class ClosureAcquisitionCommandTests(unittest.TestCase):
    setUp = ClosureCommandBoundaryTests.setUp
    remove_context = ClosureCommandBoundaryTests.remove_context
    invoke = ClosureCommandBoundaryTests.invoke
    first = ClosureExecutionContextTests.first
    rejected = ClosureExecutionContextTests.rejected
    context_bytes = ClosureExecutionContextTests.context_bytes

    def acquire_failure(self):
        self.first()
        response = self.invoke('acquire-live-release')
        self.rejected(response, 'lcer.closure_command_failed')
        return response, self.context_root / 'case-0001/command'

    def test_frozen_acquire_argv_runs_and_its_actual_guard_denial_is_retained(self):
        response, directory = self.acquire_failure()
        started = parse_stored_json((directory / 'started.json').read_bytes())
        result = parse_stored_json((directory / 'result.json').read_bytes())
        argv = json.loads(CONTRACT_PATH.read_bytes())['planned_commands']['acquire']
        expected = [item.format(absolute_unique_temp_root=str(directory/'runtime'),
                                fresh_output_root=str(directory/'output')) for item in argv]
        self.assertEqual(started['argv'], expected)
        self.assertEqual(result['capture']['argv'], expected)
        self.assertEqual(result['capture']['process']['argv'][1:], expected[1:])
        self.assertEqual(result['capture']['exit_code'], 2)
        self.assertTrue(result['capture']['capture_complete'])
        self.assertIsNone(result['capture']['timeout_seconds'])
        self.assertIn(b'lcer.acquisition_implementation_incomplete', (directory/'stderr').read_bytes())
        self.assertFalse((directory/'runtime').exists())
        self.assertFalse((directory/'output').exists())
        observed = json.loads(response.stdout)['observed']
        self.assertEqual(observed['command_exit_code'], 2)
        for name in ('stdout', 'stderr'):
            self.assertEqual(observed['command_'+name+'_sha256'], hashlib.sha256((directory/name).read_bytes()).hexdigest())

    def test_failed_command_cannot_be_rerun_in_the_same_slot(self):
        self.acquire_failure()
        before = self.context_bytes()
        self.rejected(self.invoke('acquire-live-release'), 'lcer.closure_context_ambiguous')
        self.assertEqual(self.context_bytes(), before)

    def test_modified_command_stderr_rejects_before_later_case_entry(self):
        _, directory = self.acquire_failure()
        path = directory/'stderr'
        path.write_bytes(path.read_bytes()+b'changed command output')
        self.rejected(self.invoke('verify-live-release'), 'lcer.closure_command_capture_changed')
        self.assertFalse((self.context_root/'case-0002').exists())

    def test_rehashed_wrong_command_cannot_replace_the_frozen_argv(self):
        _, directory = self.acquire_failure()
        start = parse_stored_json((directory/'started.json').read_bytes())
        start['argv'].append('--undeclared')
        (directory/'started.json').write_bytes(stored_json_bytes(start))
        result = parse_stored_json((directory/'result.json').read_bytes())
        result['started_sha256'] = hashlib.sha256((directory/'started.json').read_bytes()).hexdigest()
        result['capture']['argv'] = start['argv']
        (directory/'result.json').write_bytes(stored_json_bytes(result))
        case = directory.parent
        outer = parse_stored_json((case/'result.json').read_bytes())
        outer['command_sha256'] = hashlib.sha256((directory/'result.json').read_bytes()).hexdigest()
        (case/'result.json').write_bytes(stored_json_bytes(outer))
        self.rejected(self.invoke('verify-live-release'), 'lcer.closure_command_capture_invalid')


if __name__ == "__main__":
    if '--closure-case' in sys.argv[1:]:
        raise SystemExit(closure_case_main())
    unittest.main()
