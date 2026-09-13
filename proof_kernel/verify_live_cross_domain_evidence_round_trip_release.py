"""Independent release bootstrap. No adjacent code runs before byte closure.

Full lifecycle verification is under implementation. Byte authentication alone
does not accept a release or establish any live execution claim.
"""
import sys
sys.dont_write_bytecode = True
sys.pycache_prefix = None

# The script directory and user package paths must not supply even a stdlib
# shadow during bootstrap. The entrypoint itself is bound by its caller.
STDLIB_DIRECTORY = (getattr(sys, "_stdlib_dir", None) or sys.base_prefix +
                    "/lib/python%d.%d" % sys.version_info[:2])
STDLIB_PATHS = (STDLIB_DIRECTORY, STDLIB_DIRECTORY + "/lib-dynload",
                STDLIB_DIRECTORY.rsplit("/", 1)[0] + "/python%d%d.zip" % sys.version_info[:2])
sys.path[:] = STDLIB_PATHS

import argparse
import ast
import base64
from collections import deque
import contextlib
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import symtable
import sysconfig

RELEASE_ROOT = Path(__file__).absolute().parents[1]
CONTRACT_PATH = "proof_kernel/live_cross_domain_evidence_round_trip_contract.json"
CONTRACT_SHA256 = "b862ceba039b1f2f418b01fe32221f14f095ce4894d163077b4eaa31dd0a8755"
SPEC_PATH = "Live Cross-Domain Evidence Round-Trip Proof - Draft.md"
SPEC_SHA256 = "ecb21d9a4b8adede4ec886ac5239404fdbc492b11eb1a3ac9d419a04d8552214"
LOCAL_MODULES = {
    "live_cross_domain_evidence_round_trip",
    "live_cross_domain_evidence_round_trip_harness",
    "verify_live_cross_domain_evidence_round_trip_release",
    "test_live_cross_domain_evidence_round_trip",
    "concurrent_external_evidence_arbitration", "kernel",
}


def require(condition, code="lcer.release_evidence_invalid"):
    if not condition:
        raise ValueError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def stored(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")


def strict_json(raw, canonical=True):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, "lcer.schema_invalid")
            value[key] = item
        return value

    def constant(_):
        raise ValueError("lcer.schema_invalid")

    def floating(text):
        value = float(text)
        require(math.isfinite(value), "lcer.schema_invalid")
        return value

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant, parse_float=floating)
        require(type(value) is dict, "lcer.schema_invalid")
        if canonical:
            require(stored(value) == raw, "lcer.schema_invalid")
        return value
    except (ValueError, UnicodeError, TypeError, OverflowError, RecursionError) as error:
        raise ValueError("lcer.schema_invalid") from error


def same_json(left, right):
    if type(left) is bool or type(right) is bool:
        return type(left) is type(right) and left == right
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return set(left) == set(right) and all(same_json(left[k], right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    return left == right


def schema_accepts(definitions, schema, value, depth=0):
    require(depth <= 200, "lcer.schema_invalid")
    if "$ref" in schema:
        reference = schema["$ref"]
        require(reference.startswith("#/$defs/") and reference[8:] in definitions, "lcer.schema_invalid")
        if not schema_accepts(definitions, definitions[reference[8:]], value, depth + 1):
            return False
    if "const" in schema and not same_json(value, schema["const"]):
        return False
    if "enum" in schema and not any(same_json(value, item) for item in schema["enum"]):
        return False
    if "oneOf" in schema:
        if sum(schema_accepts(definitions, branch, value, depth + 1) for branch in schema["oneOf"]) != 1:
            return False
    kind = schema.get("type")
    if kind == "object":
        return (type(value) is dict and set(schema["required"]) <= set(value)
                and set(value) <= set(schema["properties"])
                and all(schema_accepts(definitions, schema["properties"][key], item, depth + 1)
                        for key, item in value.items()))
    if kind == "array":
        return type(value) is list and all(schema_accepts(definitions, schema["items"], item, depth + 1) for item in value)
    if kind == "string":
        return (type(value) is str and len(value) >= schema.get("minLength", 0)
                and ("pattern" not in schema or re.search(schema["pattern"], value) is not None))
    if kind == "integer":
        return ((type(value) is int or (type(value) is float and math.isfinite(value) and value.is_integer()))
                and schema.get("minimum", -math.inf) <= value <= schema.get("maximum", math.inf))
    if kind == "boolean":
        return type(value) is bool
    if kind == "null":
        return value is None
    require(kind is None, "lcer.schema_invalid")
    return True


def wire(policy, name, raw):
    value = strict_json(raw)
    definitions = policy["wire_schemas"]
    require(schema_accepts(definitions, definitions[name], value), "lcer.schema_invalid")
    return value


def ordinary_file(root, relative):
    root = Path(root).absolute()
    name = Path(relative)
    path = root / name
    require(root == root.resolve() and not name.is_absolute() and ".." not in name.parts
            and bool(name.parts) and path.resolve().is_relative_to(root)
            and not any(item.is_symlink() for item in [path, *path.parents]) and path.is_file())
    return path.read_bytes()


def manifest_entries(raw, members):
    try:
        lines = raw.decode("ascii").splitlines(keepends=True)
    except UnicodeError as error:
        raise ValueError("lcer.release_evidence_invalid") from error
    records = []
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\r\n]+)\n", line)
        require(match is not None)
        records.append((match[2], match[1]))
    require(len(records) == len(members) == 289)
    require([name for name, _ in records] == sorted(members) and len(set(members)) == len(members))
    return dict(records)


def check_index(rows, expected_paths, artifacts):
    require(type(rows) is list and len(rows) == len(expected_paths))
    names = []
    for row in rows:
        require(type(row) is dict and set(row) == {"path", "sha256", "size_bytes"})
        name = row["path"]
        require(name in expected_paths and name in artifacts)
        require(row["sha256"] == digest(artifacts[name]) and type(row["size_bytes"]) is int
                and row["size_bytes"] == len(artifacts[name]))
        names.append(name)
    require(len(set(names)) == len(names) and set(names) == set(expected_paths))


def authenticate_release(release_root, artifact_root):
    """Recalculate the closed byte graph. This function executes no local module."""
    root, artifact_root = Path(release_root).absolute(), Path(artifact_root).absolute()
    contract_raw = ordinary_file(root, CONTRACT_PATH)
    require(digest(contract_raw) == CONTRACT_SHA256)
    policy = strict_json(contract_raw, canonical=False)
    manifest_raw = ordinary_file(root, policy["release_manifest"])
    members = manifest_entries(manifest_raw, policy["release_members"])
    prefix = policy["runtime"]["output_root"] + "/"
    artifact_names = policy["artifact_relative_paths"]
    require(set(name[len(prefix):] for name in members if name.startswith(prefix)) == set(artifact_names))
    require(artifact_root == artifact_root.resolve() and artifact_root.is_dir()
            and not any(path.is_symlink() for path in [artifact_root, *artifact_root.parents]))
    found = []
    for path in artifact_root.rglob("*"):
        require(not path.is_symlink())
        if path.is_file():
            found.append(path.relative_to(artifact_root).as_posix())
    require(len(found) == 219 and set(found) == set(artifact_names))
    artifacts = {}
    for name in artifact_names:
        raw = ordinary_file(artifact_root, name)
        require(digest(raw) == members[prefix + name])
        artifacts[name] = raw
    # Verify graph membership and every backward raw-byte edge before reading
    # any executable source. Schema parsing here uses only this stdlib bootstrap.
    graph = policy["artifact_hash_graph"]
    acquisition = wire(policy, "acquisition_record", artifacts["acquisition.json"])
    require(acquisition["artifact_members"] == artifact_names)
    check_index(acquisition["artifact_hashes"], graph["acquisition_targets"], artifacts)
    require([row["witness_id"] for row in acquisition["cases"]] == graph["case_ids"])
    for row in acquisition["cases"]:
        name = row["witness_id"]; record_path = name + "/record.json"
        require(row["record_path"] == record_path and row["record_sha256"] == digest(artifacts[record_path]))
        case = wire(policy, "case_record", artifacts[record_path])
        check_index(case["artifact_sha256"], graph["case_record_targets"][name], artifacts)
    build = wire(policy, "build_record", artifacts["build.json"])
    require(acquisition["build_sha256"] == digest(artifacts["build.json"]))
    check_index([build["log"]], ["build.log"], artifacts)
    immutable = {**policy["predecessors"], **policy["unchanged_dependencies"],
                 CONTRACT_PATH: CONTRACT_SHA256, SPEC_PATH: SPEC_SHA256}
    source_bytes = {}
    for name, expected in members.items():
        if name.startswith(prefix):
            continue
        raw = ordinary_file(root, name)
        require(digest(raw) == expected)
        if name in immutable:
            require(expected == immutable[name])
        source_bytes[name] = raw
    require(set(immutable) <= set(source_bytes) and len(source_bytes) == 70)
    for symbol in ("R0", "R1", "QA", "QB"):
        original = "proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_" + symbol + ".json"
        require(digest(artifacts["canonical/" + symbol + ".json"]) == policy["canonical_records"][original])
    return {"policy": policy, "root": root, "artifact_root": artifact_root,
            "manifest_sha256": digest(manifest_raw), "members": members,
            "artifacts": artifacts, "source_bytes": source_bytes}


def native_file_image_headers(raw):
    """Derive UUID/architecture/type from every thin or universal file slice.

    This reads load-command identity only. It does not load the image, prove
    that a process mapped it, or establish native class/symbol semantics.
    """
    require(type(raw) is bytes, 'lcer.image_identity_invalid')

    def unpack(form, offset, end=None):
        size = struct.calcsize(form)
        limit = len(raw) if end is None else end
        require(0 <= offset <= limit and size <= limit - offset, 'lcer.image_identity_invalid')
        return struct.unpack_from(form, raw, offset)

    magic = raw[:4]
    slices = []
    if magic == b'\xcf\xfa\xed\xfe':
        slices.append((0, len(raw), None, None))
    else:
        require(magic in (b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf'), 'lcer.image_identity_invalid')
        count, = unpack('>I', 4)
        require(1 <= count <= 32, 'lcer.image_identity_invalid')
        wide = magic == b'\xca\xfe\xba\xbf'
        width = 32 if wide else 20
        for index in range(count):
            row = unpack('>iiQQII' if wide else '>iiIII', 8 + width * index)
            cpu, subtype, offset, size, alignment = row[:5]
            require(alignment <= 31 and offset % (1 << alignment) == 0 and offset >= 8 + count * width
                    and size >= 32 and offset <= len(raw) and size <= len(raw) - offset
                    and (not wide or row[5] == 0), 'lcer.image_identity_invalid')
            slices.append((offset, size, cpu, subtype))
        ordered = sorted(slices)
        require(all(a[0] + a[1] <= b[0] for a, b in zip(ordered, ordered[1:])), 'lcer.image_identity_invalid')
    result = []
    for offset, size, expected_cpu, expected_subtype in slices:
        end = offset + size
        magic, cpu, subtype, file_type, count, command_size, flags, reserved = unpack('<IiiIIIII', offset, end)
        require(magic == 0xfeedfacf and reserved == 0 and file_type in (2, 6, 7, 8)
                and (expected_cpu is None or (cpu, subtype) == (expected_cpu, expected_subtype))
                and 1 <= count <= command_size // 8 and command_size <= size - 32, 'lcer.image_identity_invalid')
        try:
            architecture = NativeMachOImage._architecture(cpu, subtype)
        except ValueError as error:
            raise ValueError('lcer.image_identity_invalid') from error
        cursor, command_end, uuid = offset + 32, offset + 32 + command_size, None
        for _ in range(count):
            kind, length = unpack('<II', cursor, command_end)
            require(length >= 8 and length % 8 == 0 and length <= command_end - cursor,
                    'lcer.image_identity_invalid')
            if kind == 0x1b:
                require(length == 24 and uuid is None, 'lcer.image_identity_invalid')
                value = raw[cursor + 8:cursor + 24].hex()
                uuid = '-'.join(value[a:b] for a, b in ((0, 8), (8, 12), (12, 16), (16, 20), (20, 32)))
            cursor += length
        require(cursor == command_end and uuid is not None, 'lcer.image_identity_invalid')
        result.append({'architecture': architecture, 'macho_uuid': uuid, 'file_type': file_type,
                       'offset': offset, 'size_bytes': size})
    require(len({row['architecture'] for row in result}) == len(result), 'lcer.image_identity_invalid')
    return sorted(result, key=lambda row: row['architecture'])


def native_file_image_identity(raw, identity):
    """Check an ARM64 process image without selecting a slice by its claimed UUID."""
    require(type(identity) is dict and set(identity) == {'realpath', 'sha256', 'macho_uuid', 'architecture', 'source'}
            and identity['source'] == 'dyld' and type(raw) is bytes and digest(raw) == identity['sha256'],
            'lcer.image_identity_invalid')
    choices = [row for row in native_file_image_headers(raw) if row['architecture'] in ('arm64', 'arm64e')]
    require(len(choices) == 1, 'lcer.image_identity_invalid')
    image = choices[0]
    require(image['architecture'] == identity['architecture'] and image['macho_uuid'] == identity['macho_uuid'],
            'lcer.image_identity_invalid')
    return dict(identity, file_type=image['file_type'])


class NativeMachOImage:
    """Decode recorded native image bytes without loading or executing them.

    The enclosing build verifier must authenticate the supplied image record.
    This reader checks its raw hash, architecture and UUID, then follows exact
    symbols and chained pointers. It does not infer native class ancestry yet.
    """

    def __init__(self, raw, identity):
        self._require(type(raw) is bytes and type(identity) is dict
                      and set(identity) == {'realpath', 'sha256', 'macho_uuid', 'architecture', 'source'}
                      and identity['source'] == 'dyld' and digest(raw) == identity['sha256'])
        self.identity = dict(identity)
        data = memoryview(raw)
        self.data = self._select_slice(data, identity['architecture'])
        header = self._unpack('<IiiIIIII', self.data, 0)
        magic, cpu, subtype, filetype, count, command_size, flags, reserved = header
        self._require(magic == 0xfeedfacf and filetype == 6 and reserved == 0
                      and self._architecture(cpu, subtype) == identity['architecture']
                      and 1 <= count <= command_size // 8 and command_size <= len(self.data) - 32)
        self.segments, self.sections, self.libraries = [], [], []
        self.symtab, self.fixups, self.function_starts, uuid = None, None, None, None
        self.install_name = None
        self._function_starts_decoded = None
        self._symbol_cache = {}
        cursor = 32
        for _ in range(count):
            kind, size = self._unpack('<II', self.data, cursor)
            self._require(size >= 8 and size % 8 == 0 and cursor + size <= 32 + command_size)
            command = self.data[cursor:cursor + size]
            if kind == 0x19:
                self._segment(command)
            elif kind == 0x1b:
                self._require(size == 24 and uuid is None)
                value = bytes(command[8:24]).hex()
                uuid = '-'.join(value[a:b] for a, b in ((0, 8), (8, 12), (12, 16), (16, 20), (20, 32)))
            elif kind == 0x2:
                self._require(size == 24 and self.symtab is None)
                self.symtab = self._unpack('<IIII', command, 8)
            elif kind == 0x80000034:
                self._require(size == 16 and self.fixups is None)
                offset, length = self._unpack('<II', command, 8)
                self.fixups = self._range(self.data, offset, length)
            elif kind == 0x26:
                self._require(size == 16 and self.function_starts is None)
                offset, length = self._unpack('<II', command, 8)
                self.function_starts = self._range(self.data, offset, length)
            elif kind in (0xc, 0xd, 0x80000018, 0x8000001f, 0x80000023, 0x20):
                self._require(size >= 24)
                offset = self._unpack('<I', command, 8)[0]
                self._require(24 <= offset < size)
                name = self._cstring(command, offset)
                self._require(bool(name))
                if kind == 0xd:
                    self._require(self.install_name is None)
                    self.install_name = name
                else:
                    self.libraries.append(name)
            cursor += size
        self._require(cursor == 32 + command_size and uuid == identity['macho_uuid']
                      and self.segments and self.symtab is not None and self.fixups is not None)
        self._nonoverlap([(row['address'], row['size']) for row in self.segments if row['size']])
        self._nonoverlap([(row['offset'], row['file_size']) for row in self.segments if row['file_size']])
        headers = [row for row in self.segments if row['offset'] == 0 and row['file_size'] >= cursor]
        self._require(len(headers) == 1)
        self.base = headers[0]['address']
        symbol_offset, symbol_count, string_offset, string_size = self.symtab
        self.symbol_bytes = self._range(self.data, symbol_offset, symbol_count * 16)
        self.string_bytes = self._range(self.data, string_offset, string_size)
        self._require(string_size > 0)
        self._fixup_tables()

    @staticmethod
    def _require(condition):
        require(condition, 'lcer.native_metadata_invalid')

    @classmethod
    def _range(cls, raw, offset, size):
        cls._require(type(offset) is int and type(size) is int and 0 <= offset <= len(raw)
                     and 0 <= size <= len(raw) - offset)
        return raw[offset:offset + size]

    @classmethod
    def _unpack(cls, form, raw, offset):
        return struct.unpack(form, cls._range(raw, offset, struct.calcsize(form)))

    @classmethod
    def _cstring(cls, raw, offset):
        cls._require(0 <= offset < len(raw))
        end = offset
        while end < len(raw) and raw[end] != 0:
            end += 1
        cls._require(end < len(raw))
        try:
            return bytes(raw[offset:end]).decode('utf-8', 'strict')
        except UnicodeError as error:
            raise ValueError('lcer.native_metadata_invalid') from error

    @staticmethod
    def _architecture(cpu, subtype):
        if cpu == 0x0100000c and subtype & 0x00ffffff in (0, 1, 2):
            return 'arm64e' if subtype & 0x00ffffff == 2 else 'arm64'
        if cpu == 0x01000007 and subtype & 0x00ffffff in (3, 8):
            return 'x86_64'
        raise ValueError('lcer.native_metadata_invalid')

    @classmethod
    def _nonoverlap(cls, ranges):
        ordered = sorted(ranges)
        cls._require(all(a + size <= b for (a, size), (b, _) in zip(ordered, ordered[1:])))

    @classmethod
    def _select_slice(cls, raw, architecture):
        magic = bytes(cls._range(raw, 0, 4))
        if magic == b'\xcf\xfa\xed\xfe':
            return raw
        cls._require(magic in (b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf'))
        count = cls._unpack('>I', raw, 4)[0]
        cls._require(1 <= count <= 32)
        wide = magic == b'\xca\xfe\xba\xbf'
        width = 32 if wide else 20
        slices, selected = [], []
        for index in range(count):
            row = cls._unpack('>iiQQII' if wide else '>iiIII', raw, 8 + index * width)
            cpu, subtype, offset, size, alignment = row[:5]
            cls._require(alignment <= 31 and offset % (1 << alignment) == 0
                         and offset >= 8 + count * width and size >= 32
                         and (not wide or row[5] == 0))
            part = cls._range(raw, offset, size)
            thin = cls._unpack('<Iii', part, 0)
            cls._require(thin == (0xfeedfacf, cpu, subtype))
            slices.append((offset, size))
            if cls._architecture(cpu, subtype) == architecture:
                selected.append(part)
        cls._nonoverlap(slices)
        cls._require(len(selected) == 1)
        return selected[0]

    def _segment(self, command):
        self._require(len(command) >= 72)
        _, size, name, address, length, offset, file_size, maximum, protection, count, flags = self._unpack(
            '<II16sQQQQiiII', command, 0)
        self._require(size == 72 + 80 * count and file_size <= length and address + length < 1 << 64)
        self._range(self.data, offset, file_size)
        name = self._cstring(name + b'\0', 0)
        self._require(name and name not in [row['name'] for row in self.segments])
        segment = {'name': name, 'address': address, 'size': length, 'offset': offset,
                   'file_size': file_size, 'protection': protection}
        self.segments.append(segment)
        for number in range(count):
            section = self._unpack('<16s16sQQIIIIIIII', command, 72 + 80 * number)
            section_name, parent, start, size, file_offset, alignment, _, _, section_flags, _, _, _ = section
            self._require(parent == command[8:24] and address <= start <= address + length
                          and size <= address + length - start and alignment <= 31)
            # Zerofill has virtual storage and no file-backed data.
            if section_flags & 0xff not in (1, 0xc, 0x12):
                self._require(offset <= file_offset <= offset + file_size
                              and size <= offset + file_size - file_offset
                              and file_offset - offset == start - address)
            self.sections.append({'name': self._cstring(section_name + b'\0', 0),
                                  'address': start, 'size': size, 'segment': segment,
                                  'flags': section_flags, 'stub_size': section[10]})

    def function_range(self, address):
        self._require(self.function_starts is not None and self.identity['architecture'] == 'arm64')
        if self._function_starts_decoded is None:
            cursor, current, starts, terminated = 0, self.base, [], False
            while cursor < len(self.function_starts):
                delta, shift = 0, 0
                while True:
                    self._require(cursor < len(self.function_starts) and shift < 64)
                    byte = self.function_starts[cursor]
                    cursor += 1
                    delta |= (byte & 127) << shift
                    if not byte & 128:
                        break
                    shift += 7
                self._require(delta < 1 << 64)
                if delta == 0:
                    self._require(all(value == 0 for value in self.function_starts[cursor:]))
                    terminated = True
                    break
                current += delta
                self._require(current < 1 << 64 and current % 4 == 0)
                starts.append(current)
            self._require(terminated)
            self._function_starts_decoded = tuple(starts)
        starts = self._function_starts_decoded
        self._require(address in starts)
        sections = [row for row in self.sections if row['address'] <= address < row['address'] + row['size']
                    and row['segment']['protection'] & 4 and row['flags'] & 0x80000400]
        self._require(len(sections) == 1)
        index = starts.index(address)
        end = sections[0]['address'] + sections[0]['size']
        if index + 1 < len(starts):
            end = min(end, starts[index + 1])
        self._require(address < end and end - address <= 65536)
        self.read(address, end - address)
        return address, end

    def call_target(self, address):
        """Resolve only an actual arm64 three-instruction symbol stub."""
        self._require(self.identity['architecture'] == 'arm64')
        sections = [row for row in self.sections if row['address'] <= address < row['address'] + row['size']
                    and row['flags'] & 0xff == 8]
        self._require(len(sections) == 1 and sections[0]['stub_size'] == 12
                      and (address - sections[0]['address']) % 12 == 0)
        adrp, load, branch = struct.unpack('<III', self.read(address, 12))
        register = adrp & 31
        self._require(adrp & 0x9f000000 == 0x90000000 and register in (16, 17)
                      and load & 0xffc00000 == 0xf9400000 and load & 31 == register
                      and load >> 5 & 31 == register and branch == 0xd61f0000 | (register << 5))
        immediate = ((adrp >> 5 & 0x7ffff) << 2) | (adrp >> 29 & 3)
        if immediate & (1 << 20):
            immediate -= 1 << 21
        page = (address & ~0xfff) + (immediate << 12)
        return self.pointer(page + (load >> 10 & 0xfff) * 8)

    def read(self, address, size):
        candidates = [row for row in self.segments if row['address'] <= address
                      and address - row['address'] <= row['file_size']
                      and 0 <= size <= row['file_size'] - (address - row['address'])]
        self._require(len(candidates) == 1)
        row = candidates[0]
        return bytes(self._range(self.data, row['offset'] + address - row['address'], size))

    def symbol(self, name):
        """Return one exact defined symbol; never infer by nearby strings."""
        return self.symbols([name])[name]

    def symbols(self, names):
        found = self.defined_symbols(names)
        self._require(set(found) == set(names))
        return found

    def defined_symbols(self, names):
        """Return requested definitions; a missing name is not a definition."""
        self._require(type(names) is list and names and all(type(name) is str and name and '\0' not in name for name in names)
                      and len(set(names)) == len(names))
        missing = [name for name in names if name not in self._symbol_cache]
        if not missing:
            return {name: self._symbol_cache[name] for name in names if self._symbol_cache[name] is not None}
        pool = bytes(self.string_bytes)
        indexes = {}
        found = {name: [] for name in missing}
        for name in missing:
            needle = name.encode('utf-8') + b'\0'
            offset = pool.find(needle, 1)
            while offset >= 0:
                indexes[offset] = name
                offset = pool.find(needle, offset + 1)
        # Mach-O permits string-table suffix sharing. Match the exact indexed
        # bytes, then require one defined symbol in its declared section.
        # The constructor bounds the complete nlist_64 table. Check its row
        # width here as well, then decode fixed-width rows without millions
        # of repeated Python range checks. Every entry still checks its
        # string index before any definition/name filter can skip it.
        self._require(len(self.symbol_bytes) % 16 == 0)
        for index, kind, section, description, address in struct.iter_unpack('<IBBHQ', self.symbol_bytes):
            self._require(index < len(self.string_bytes))
            if index not in indexes or kind & 0xe0 or kind & 0x0e != 0x0e:
                continue
            self._require(1 <= section <= len(self.sections) and description & 0x80 == 0)
            row = self.sections[section - 1]
            self._require(row['address'] <= address < row['address'] + row['size'])
            found[indexes[index]].append(address)
        self._require(all(len(values) <= 1 for values in found.values()))
        self._symbol_cache.update({name: values[0] if values else None for name, values in found.items()})
        return {name: self._symbol_cache[name] for name in names if self._symbol_cache[name] is not None}

    def _fixup_tables(self):
        version, starts, imports, symbols, count, form, symbol_form = self._unpack('<7I', self.fixups, 0)
        self._require(version == 0 and symbol_form == 0 and form in (1, 2, 3)
                      and min(starts, imports, symbols) >= 28)
        width = {1: 4, 2: 8, 3: 16}[form]
        self.imports = self._range(self.fixups, imports, count * width)
        self.import_names = self._range(self.fixups, symbols, len(self.fixups) - symbols)
        self.import_form, self.import_width = form, width
        segment_count = self._unpack('<I', self.fixups, starts)[0]
        self._require(segment_count == len(self.segments))
        offsets = self._unpack('<' + 'I' * segment_count, self.fixups, starts + 4)
        self.starts = []
        for segment, relative in zip(self.segments, offsets):
            if relative == 0:
                self.starts.append(None)
                continue
            self._require(relative >= 4 + 4 * segment_count)
            size, page_size, pointer_form, segment_offset, maximum, page_count = self._unpack(
                '<IHHQIH', self.fixups, starts + relative)
            self._require(size >= 22 + 2 * page_count and page_size in (0x1000, 0x4000)
                          and pointer_form == 6 and maximum == 0
                          and segment_offset == segment['address'] - self.base
                          and page_count <= (segment['size'] + page_size - 1) // page_size)
            table = self._range(self.fixups, starts + relative, size)
            pages = self._unpack('<' + 'H' * page_count, table, 22)
            self._require(all(value == 0xffff or value < page_size for value in pages))
            self.starts.append((page_size, pages))

    def _import(self, index, pointer_addend):
        self._require(index < len(self.imports) // self.import_width)
        offset = index * self.import_width
        if self.import_form == 3:
            word, addend = self._unpack('<Qq', self.imports, offset)
            ordinal, weak, name = word & 0xffff, bool((word >> 16) & 1), word >> 32
            self._require(word >> 17 & 0x7fff == 0)
        else:
            word = self._unpack('<I', self.imports, offset)[0]
            ordinal, weak, name = word & 0xff, bool((word >> 8) & 1), word >> 9
            addend = self._unpack('<i', self.imports, offset + 4)[0] if self.import_form == 2 else 0
        # Special/flat/self lookup and weak resolution need a separate proof.
        self._require(1 <= ordinal <= len(self.libraries) and not weak)
        symbol = self._cstring(self.import_names, name)
        self._require(bool(symbol))
        return {'kind': 'bind', 'library': self.libraries[ordinal - 1],
                'symbol': symbol, 'addend': addend + pointer_addend}

    def pointer(self, address):
        """Resolve a real chained pointer or an actual unchained null slot."""
        candidates = [(index, row) for index, row in enumerate(self.segments)
                      if row['address'] <= address and address + 8 <= row['address'] + row['file_size']]
        self._require(len(candidates) == 1 and address % 4 == 0)
        index, segment = candidates[0]
        table = self.starts[index]
        word = struct.unpack('<Q', self.read(address, 8))[0]
        if table is not None:
            page_size, pages = table
            page = (address - segment['address']) // page_size
            if page < len(pages) and pages[page] != 0xffff:
                page_base = segment['address'] + page * page_size
                position = page_base + pages[page]
                while position <= address:
                    self._require(position + 8 <= page_base + page_size)
                    encoded = struct.unpack('<Q', self.read(position, 8))[0]
                    if position == address:
                        if encoded >> 63:
                            self._require(encoded >> 32 & 0x7ffff == 0)
                            return self._import(encoded & 0xffffff, encoded >> 24 & 0xff)
                        self._require(encoded >> 44 & 0x7f == 0)
                        target = (encoded & ((1 << 36) - 1)) | ((encoded >> 36 & 0xff) << 56)
                        target += self.base
                        self.read(target, 1)
                        return {'kind': 'rebase', 'address': target}
                    step = (encoded >> 51 & 0xfff) * 4
                    if step == 0:
                        break
                    position += step
        self._require(word == 0)
        return {'kind': 'null'}


def native_cpp_tokens(raw):
    """Read C++ tokens after physical line splicing; never evaluate a macro."""
    try:
        source = raw.decode('utf-8', 'strict').replace('\\\r\n', '').replace('\\\n', '')
    except (UnicodeError, AttributeError) as error:
        raise ValueError('lcer.native_metadata_invalid') from error
    tokens, cursor = [], 0
    pattern = re.compile(r'\s+|//[^\n]*|/\*[\s\S]*?\*/|"(?:\\[\s\S]|[^"\\])*"|\'(?:\\[\s\S]|[^\'\\])*\'|[A-Za-z_][A-Za-z_0-9]*|[^\s]')
    while cursor < len(source):
        match = pattern.match(source, cursor)
        require(match is not None, 'lcer.native_metadata_invalid')
        token = match[0]
        require(not (source.startswith('/*', cursor) and not token.endswith('*/'))
                and not (source[cursor] in ('"', "'") and len(token) == 1)
                and '\0' not in token, 'lcer.native_metadata_invalid')
        if not token.isspace() and not token.startswith(('//', '/*')):
            tokens.append(token)
        cursor = match.end()
    return tokens


def generated_class_declarations(raw):
    """Extract declared C++ parent/package relationships from UHT bytes.

    The caller must bind those bytes to the actual build-input inventory.
    Reflected names still come from the native constructor arguments.
    """
    tokens = native_cpp_tokens(raw)
    declarations = []
    for index, token in enumerate(tokens):
        if token != 'DECLARE_CLASS2':
            continue
        require(tokens[max(0, index - 2):index] != ['#', 'define']
                and tokens[index + 1:index + 2] == ['('], 'lcer.native_metadata_invalid')
        stack, arguments, current = ['('], [], []
        for item in tokens[index + 2:]:
            if item in ('(', '[', '{'):
                stack.append(item)
            elif item in (')', ']', '}'):
                require(stack and stack.pop() == {')': '(', ']': '[', '}': '{'}[item], 'lcer.native_metadata_invalid')
                if not stack:
                    arguments.append(current)
                    break
            if item == ',' and len(stack) == 1:
                arguments.append(current)
                current = []
            else:
                current.append(item)
        require(not stack and len(arguments) == 6, 'lcer.native_metadata_invalid')
        cpp, parent, flags, cast_flags, package, constructor = arguments
        identifier = lambda values: len(values) == 1 and re.fullmatch('[A-Za-z_][A-Za-z_0-9]*', values[0]) is not None
        require(identifier(cpp) and identifier(parent) and bool(flags) and bool(cast_flags)
                and constructor == ['Z_Construct_UClass_' + cpp[0]]
                and len(package) == 4 and package[:2] == ['TEXT', '('] and package[3] == ')'
                and re.fullmatch('"/Script/[A-Za-z_][A-Za-z_0-9]*"', package[2]) is not None,
                'lcer.native_metadata_invalid')
        row = {'cpp_name': cpp[0], 'cpp_parent': parent[0], 'package': package[2][1:-1],
               'constructor': constructor[0]}
        require(not any(old['cpp_name'] == row['cpp_name'] for old in declarations), 'lcer.native_metadata_invalid')
        declarations.append(row)
    return declarations


def native_class_parameter_layout(raw):
    """Check the generated registration ABI against its supplied header bytes."""
    fields = [
        'UClass* (*ClassNoRegisterFunc)(ETypeConstructPhase);',
        'const char* ClassConfigNameUTF8;',
        'const FCppClassTypeInfoStatic* CppClassInfo;',
        'FTypeConstructFunc* const* DependencySingletonFuncArray;',
        'const FClassFunctionLinkInfo* FunctionLinkArray;',
        'const FPropertyParamsBase* const* PropertyArray;',
        'const FImplementedInterfaceParams* ImplementedInterfaceArray;']
    prefix = native_cpp_tokens(('struct FClassParams {' + ''.join(fields)
                                + 'uint32 NumDependencySingletons : 4; uint32 NumFunctions : 11;'
                                + 'uint32 NumProperties : 11; uint32 NumImplementedInterfaces : 6;').encode())
    tokens = native_cpp_tokens(raw)
    found = [index for index in range(len(tokens)) if tokens[index:index + len(prefix)] == prefix]
    require(len(found) == 1, 'lcer.native_metadata_invalid')
    # Each preceding field is one pointer in the supported 64-bit ABI.
    return {'self': 0, 'dependencies': 3 * 8, 'dependency_count': len(fields) * 8,
            'header_sha256': digest(raw)}


def declared_native_registration(image, declaration, layout_raw):
    """Join compiled registration data to a generated C++ declaration.

    Input inventory authentication and cross-image ancestry closure remain
    the enclosing verifier's responsibility. No source file is executed.
    """
    require(type(declaration) is dict and set(declaration) == {'cpp_name', 'cpp_parent', 'package', 'constructor'}
            and all(type(value) is str and value for value in declaration.values())
            and declaration['constructor'] == 'Z_Construct_UClass_' + declaration['cpp_name'],
            'lcer.native_metadata_invalid')
    function = declaration['constructor']
    symbol = '__Z' + str(len(function)) + function + '19ETypeConstructPhase'
    address = image.symbol(symbol)
    record = Arm64ClassRegistration(image, address).decode()
    require(record['package'] == declaration['package'], 'lcer.native_metadata_invalid')
    layout = native_class_parameter_layout(layout_raw)
    parameters = record['class_params']
    require(image.pointer(parameters + layout['self']) == {'kind': 'rebase', 'address': address},
            'lcer.native_metadata_invalid')
    count = image.read(parameters + layout['dependency_count'], 1)[0] & 15
    require(count in (1, 2), 'lcer.native_metadata_invalid')
    pointer = image.pointer(parameters + layout['dependencies'])
    require(pointer['kind'] == 'rebase', 'lcer.native_metadata_invalid')
    dependencies = [image.pointer(pointer['address'] + number * 8) for number in range(count)]
    require(all(row['kind'] in ('rebase', 'bind') for row in dependencies), 'lcer.native_metadata_invalid')
    return {**record, 'cpp_name': declaration['cpp_name'], 'cpp_parent': declaration['cpp_parent'],
            'super_constructor': dependencies[0] if count == 2 else None,
            'package_constructor': dependencies[-1], 'layout_sha256': layout['header_sha256']}


class Arm64ClassRegistration:
    """Interpret the bounded generated registration function as data.

    Both construction phases and both outcomes of unknown cache reads are
    followed. Only the two declared registration calls may leave the function.
    Unsupported instructions or writes outside its stack frame reject.
    """

    PRIVATE = ('__Z25GetPrivateStaticClassBodyPKDsS0_RP6UClassPFvvEjj11EClassFlags15EClassCastFlagsS0_'
               'PFvRK18FObjectInitializerEPFP7UObjectR13FVTableHelperEO31FUObjectCppClassStaticFunctionsPFS2_vESM_')
    CONSTRUCT = '__ZN17UECodeGen_Private15ConstructUClassERP6UClassRKNS_12FClassParamsE'
    PRIVATE_HELPER = ('__ZN17UECodeGen_Private27ConstructUClassNoInitHelperI6UClassZ25GetPrivateStaticClassBody'
                      'PKDsS3_RPS1_PFvvEjj11EClassFlags15EClassCastFlagsS3_PFvRK18FObjectInitializerE'
                      'PFP7UObjectR13FVTableHelperEO31FUObjectCppClassStaticFunctionsPFS4_vESO_E3$_0EE'
                      'vS3_S3_S5_S7_jjS8_S9_S3_SE_SK_SM_SO_SO_OT0_')
    LIBRARY = '@rpath/libUnrealEditor-CoreUObject.dylib'

    def __init__(self, image, address):
        NativeMachOImage._require(isinstance(image, NativeMachOImage))
        self.image = image
        self.start, self.end = image.function_range(address)
        self._direct = {}
        if Path(image.identity['realpath']).name == 'libUnrealEditor-CoreUObject.dylib':
            symbols = image.symbols([self.PRIVATE, self.CONSTRUCT, self.PRIVATE_HELPER])
            self._direct = {symbols[key]: key for key in (self.PRIVATE, self.CONSTRUCT)}
            self._private_forwarding(symbols[self.PRIVATE], symbols[self.PRIVATE_HELPER])
            self._direct[symbols[self.PRIVATE_HELPER]] = self.PRIVATE

    def _private_forwarding(self, address, helper):
        """Prove the installed private-body wrapper preserves its arguments.

        UField's optimized code calls the same helper directly. The wrapper
        may only copy its six stack arguments through scratch X/Q registers
        and tail-branch to the exact helper symbol. Every byte must survive.
        The integer argument registers, SP, LR and callee-saved state cannot
        change. Unsupported instructions or any other branch reject.
        """
        start, end = self.image.function_range(address)
        self._require(end - start <= 256 and helper != start)
        self._require(self.image.function_range(helper)[0] == helper)
        memory = list(range(48))  # Six eight-byte arguments after x0..x7.
        registers = {}
        for pc in range(start, end, 4):
            instruction = struct.unpack('<I', self.image.read(pc, 4))[0]
            if instruction & 0xfc000000 == 0x14000000:  # B, not BL.
                target = pc + (self._signed(instruction & 0x3ffffff, 26) << 2)
                self._require(pc + 4 == end and target == helper and memory == list(range(48)))
                return
            unsigned = instruction & 0xffc00000
            unscaled = instruction & 0xffe00c00
            if unsigned in (0xf9400000, 0xf9000000, 0x3dc00000, 0x3d800000):
                vector = bool(instruction & (1 << 26))
                width = 16 if vector else 8
                offset = (instruction >> 10 & 0xfff) * width
            elif unscaled in (0xf8400000, 0xf8000000, 0x3cc00000, 0x3c800000):
                vector = bool(instruction & (1 << 26))
                width = 16 if vector else 8
                offset = self._signed(instruction >> 12 & 0x1ff, 9)
            else:
                raise ValueError('lcer.native_registration_unclassified')
            number, base = instruction & 31, instruction >> 5 & 31
            self._require(base == 31 and 0 <= offset <= 48 - width
                          and (0 <= number <= 7 if vector else 8 <= number <= 17))
            key = ('q' if vector else 'x', number)
            if instruction & (1 << 22):
                registers[key] = list(memory[offset:offset + width])
            else:
                self._require(key in registers and len(registers[key]) == width)
                memory[offset:offset + width] = registers[key]
        raise ValueError('lcer.native_registration_unclassified')

    @staticmethod
    def _signed(value, width):
        return value - (1 << width) if value & (1 << (width - 1)) else value

    @staticmethod
    def _require(condition):
        require(condition, 'lcer.native_registration_unclassified')

    def _target(self, address):
        if address in self._direct:
            return self._direct[address]
        target = self.image.call_target(address)
        self._require(target['kind'] == 'bind' and target['library'] == self.LIBRARY
                      and target['addend'] == 0 and target['symbol'] in (self.PRIVATE, self.CONSTRUCT))
        return target['symbol']

    def _wide_string(self, address):
        self._require(type(address) is int and address % 2 == 0)
        result = bytearray()
        for offset in range(0, 2048, 2):
            sections = [row for row in self.image.sections if row['address'] <= address + offset
                        and address + offset + 2 <= row['address'] + row['size']
                        and not row['segment']['protection'] & 2]
            self._require(len(sections) == 1)
            raw = self.image.read(address + offset, 2)
            if raw == b'\0\0':
                try:
                    return result.decode('utf-16le', 'strict')
                except UnicodeError as error:
                    raise ValueError('lcer.native_registration_unclassified') from error
            result.extend(raw)
        raise ValueError('lcer.native_registration_unclassified')

    @staticmethod
    def _shift(value, amount):
        if type(value) is int:
            return value + amount
        if type(value) is tuple and value[0] == 'stack':
            return ('stack', value[1] + amount)
        return ('unknown',)

    def _phase(self, phase):
        initial = [('entry', number) for number in range(31)] + [('stack', 0)]
        initial[0] = phase
        pending = [(self.start, initial, {}, [], frozenset())]
        returned = []
        while pending:
            self._require(len(pending) + len(returned) <= 16)
            pc, registers, stack, calls, visited = pending.pop()
            while True:
                self._require(self.start <= pc < self.end and pc % 4 == 0 and pc not in visited and len(visited) < 256)
                visited = visited | {pc}
                instruction = struct.unpack('<I', self.image.read(pc, 4))[0]
                next_pc = pc + 4

                def reg(number, width=64, stack_register=False):
                    value = registers[number] if number != 31 or stack_register else 0
                    return value & ((1 << width) - 1) if type(value) is int else value

                def put(number, value, width=64, stack_register=False):
                    if number != 31 or stack_register:
                        registers[number] = value & ((1 << width) - 1) if type(value) is int else value

                def access(base, offset, size, value=None, store=False):
                    address = self._shift(base, offset)
                    if type(address) is tuple and address[0] == 'stack':
                        position = address[1]
                        self._require(type(registers[31]) is tuple and registers[31][0] == 'stack'
                                      and -4096 <= registers[31][1] <= position and position + size <= 0)
                        if store:
                            for key in list(stack):
                                if key[0] < position + size and position < key[0] + key[1]:
                                    del stack[key]
                            stack[position, size] = value
                            return None
                        return stack.get((position, size), ('unknown',))
                    self._require(not store and type(address) is int)
                    segments = [row for row in self.image.segments if row['address'] <= address
                                and address + size <= row['address'] + row['size']]
                    self._require(len(segments) == 1)
                    return ('load', address, size)

                if instruction == 0xd503201f:  # NOP
                    pass
                elif instruction & 0x1f000000 == 0x10000000:  # ADR / ADRP
                    immediate = ((instruction >> 5 & 0x7ffff) << 2) | (instruction >> 29 & 3)
                    delta = self._signed(immediate, 21)
                    value = (pc & ~0xfff) + (delta << 12) if instruction >> 31 else pc + delta
                    put(instruction & 31, value)
                elif instruction & 0x1f000000 == 0x11000000:  # ADD/SUB immediate, without flags
                    self._require(not instruction & (1 << 29) and not instruction & (1 << 23))
                    width = 64 if instruction >> 31 else 32
                    amount = (instruction >> 10 & 0xfff) << (12 if instruction & (1 << 22) else 0)
                    if instruction & (1 << 30):
                        amount = -amount
                    source, destination = instruction >> 5 & 31, instruction & 31
                    self._require(width == 64 or (source != 31 and destination != 31))
                    value = self._shift(reg(source, width, True), amount)
                    put(destination, value, width, True)
                    if destination == 31:
                        self._require(type(value) is tuple and value[0] == 'stack'
                                      and -4096 <= value[1] <= 0 and value[1] % 16 == 0)
                elif instruction & 0x1f800000 == 0x12800000:  # MOVN / MOVZ / MOVK
                    width = 64 if instruction >> 31 else 32
                    operation, shift = instruction >> 29 & 3, (instruction >> 21 & 3) * 16
                    self._require(operation in (0, 2, 3) and shift < width)
                    value = (instruction >> 5 & 0xffff) << shift
                    destination = instruction & 31
                    if operation == 0:
                        value = ~value
                    elif operation == 3:
                        old = reg(destination, width)
                        value = (old & ~(0xffff << shift)) | value if type(old) is int else ('unknown',)
                    put(destination, value, width)
                elif instruction & 0x7fe0ffe0 == 0x2a0003e0:  # MOV register (ORR with ZR)
                    width = 64 if instruction >> 31 else 32
                    put(instruction & 31, reg(instruction >> 16 & 31, width), width)
                elif instruction & 0x3b000000 == 0x39000000:  # Unsigned immediate LDR/STR
                    size, operation = 1 << (instruction >> 30), instruction >> 22 & 3
                    self._require(operation in (0, 1) and not instruction & (1 << 26))
                    destination, source = instruction & 31, instruction >> 5 & 31
                    offset = (instruction >> 10 & 0xfff) * size
                    value = access(reg(source, stack_register=True), offset, size,
                                   reg(destination, size * 8), store=operation == 0)
                    if operation == 1:
                        put(destination, value, size * 8)
                elif instruction & 0x3a000000 == 0x28000000:  # Integer LDP/STP
                    operation, mode = instruction >> 22 & 1, instruction >> 23 & 3
                    width_code = instruction >> 30
                    self._require(width_code in (0, 2) and mode in (1, 2, 3) and not instruction & (1 << 26))
                    size = 8 if width_code == 2 else 4
                    first, second, source = instruction & 31, instruction >> 10 & 31, instruction >> 5 & 31
                    offset = self._signed(instruction >> 15 & 127, 7) * size
                    base = reg(source, stack_register=True)
                    if mode == 3:
                        base = self._shift(base, offset)
                        put(source, base, stack_register=True)
                    effective = 0 if mode in (1, 3) else offset
                    left = access(base, effective, size, reg(first, size * 8), store=operation == 0)
                    right = access(base, effective + size, size, reg(second, size * 8), store=operation == 0)
                    if operation:
                        put(first, left, size * 8); put(second, right, size * 8)
                    if mode == 1:
                        put(source, self._shift(base, offset), stack_register=True)
                elif instruction & 0x7e000000 == 0x34000000:  # CBZ / CBNZ
                    target = pc + (self._signed(instruction >> 5 & 0x7ffff, 19) << 2)
                    value = reg(instruction & 31, 64 if instruction >> 31 else 32)
                    nonzero = bool(instruction & (1 << 24))
                    if type(value) is int:
                        next_pc = target if bool(value) == nonzero else next_pc
                    else:
                        pending.append((target, list(registers), dict(stack), list(calls), visited))
                elif instruction & 0x7c000000 == 0x14000000:  # B / BL
                    target = pc + (self._signed(instruction & 0x3ffffff, 26) << 2)
                    if not instruction >> 31:
                        next_pc = target
                    else:
                        callee = self._target(target)
                        self._require(not calls)
                        if callee == self.PRIVATE:
                            self._require(phase == 0 and type(reg(2)) is int)
                            package, name = self._wide_string(reg(0)), self._wide_string(reg(1))
                            self._require(re.fullmatch('/Script/[A-Za-z_][A-Za-z_0-9]*', package) is not None
                                          and re.fullmatch('[A-Za-z_][A-Za-z_0-9]*', name) is not None)
                            calls.append({'operation': 'private', 'package': package, 'name': name,
                                          'singleton': reg(2), 'call_address': pc})
                        else:
                            self._require(phase == 1 and type(reg(0)) is int and type(reg(1)) is int)
                            calls.append({'operation': 'construct', 'singleton': reg(0),
                                          'class_params': reg(1), 'call_address': pc})
                        for number in range(19):
                            registers[number] = ('call_result', pc, number)
                        registers[30] = ('return_from_call', next_pc)
                elif instruction == 0xd65f03c0:  # RET x30
                    self._require(registers[31] == ('stack', 0) and registers[30] == initial[30]
                                  and registers[19:30] == initial[19:30])
                    self._require(type(reg(0)) is tuple and reg(0)[0] == 'load' and reg(0)[2] == 8)
                    returned.append({'calls': calls, 'return_slot': reg(0)[1]})
                    break
                else:
                    raise ValueError('lcer.native_registration_unclassified')
                pc = next_pc
        self._require(returned)
        events = [row['calls'][0] for row in returned if row['calls']]
        self._require(events and all(event == events[0] for event in events)
                      and all(row['return_slot'] == events[0]['singleton'] for row in returned))
        return events[0]

    def decode(self):
        inner, outer = self._phase(0), self._phase(1)
        self._require(inner['operation'] == 'private' and outer['operation'] == 'construct'
                      and inner['singleton'] != outer['singleton'])
        self._require(self.image.pointer(outer['class_params']) == {'kind': 'rebase', 'address': self.start})
        return {'class_path': inner['package'] + '.' + inner['name'], 'package': inner['package'],
                'reflected_name': inner['name'], 'constructor_address': self.start,
                'class_params': outer['class_params'], 'inner': inner, 'outer': outer}


class NativeClassRegistry:
    """Close native parent links using supplied image and build-input bytes.

    The enclosing verifier must first establish complete executed inventories
    and authenticate those external records. This constructor rechecks the
    supplied bytes and derives all available declared classes. It never treats
    missing metadata as evidence that an observed Actor is harmless.
    """

    def __init__(self, images, file_records, source_bytes, layout_path):
        self._require(type(images) is list and images and all(isinstance(image, NativeMachOImage) for image in images))
        self._require(len({image.identity['realpath'] for image in images}) == len(images)
                      and all(image.identity['architecture'] == 'arm64' and image.install_name for image in images)
                      and len({image.install_name for image in images}) == len(images))
        self._images = {image.identity['realpath']: image for image in images}
        self._require(type(file_records) is list and type(source_bytes) is dict and type(layout_path) is str)
        inputs = {}
        for row in file_records:
            self._require(type(row) is dict and set(row) == {'realpath', 'sha256', 'size_bytes'}
                          and type(row['realpath']) is str and Path(row['realpath']).is_absolute()
                          and '..' not in Path(row['realpath']).parts
                          and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']) is not None
                          and type(row['size_bytes']) is int and row['size_bytes'] >= 0 and row['realpath'] not in inputs)
            inputs[row['realpath']] = row
        generated = {name for name in inputs if name.endswith('.generated.h')}
        self._require(generated and layout_path in inputs and set(source_bytes) == generated | {layout_path})
        for name, raw in source_bytes.items():
            self._require(type(raw) is bytes and digest(raw) == inputs[name]['sha256'] and len(raw) == inputs[name]['size_bytes'])
        layout = source_bytes[layout_path]
        native_class_parameter_layout(layout)
        declarations = {}
        for name in sorted(generated):
            for row in generated_class_declarations(source_bytes[name]):
                self._require(row['cpp_name'] not in declarations)
                declarations[row['cpp_name']] = row
        self._require(declarations)
        symbols = {name: self._symbol(row['constructor']) for name, row in declarations.items()}
        definitions = {path: image.defined_symbols(list(symbols.values())) for path, image in self._images.items()}
        owners, records = {}, {}
        for name, symbol in symbols.items():
            matches = [path for path, values in definitions.items() if symbol in values]
            self._require(len(matches) <= 1)
            if matches:
                owners[name] = matches[0]
                records[name] = declared_native_registration(self._images[matches[0]], declarations[name], layout)
        self._require(records)
        packages = sorted({record['package'] for record in records.values()})
        package_symbols = {package: self._symbol('Z_Construct_UPackage__' + package[1:].replace('/', '_'))
                           for package in packages}
        package_definitions = {path: image.defined_symbols(list(package_symbols.values())) for path, image in self._images.items()}
        package_owners = {}
        for package, symbol in package_symbols.items():
            matches = [path for path, values in package_definitions.items() if symbol in values]
            self._require(len(matches) == 1)
            package_owners[package] = matches[0]
        paths = [record['class_path'] for record in records.values()]
        self._require(len(paths) == len(set(paths)))
        parents = {}
        for name, record in records.items():
            owner = owners[name]
            package = record['package']
            target_owner = package_owners[package]
            self._pointer_to(owner, record['package_constructor'], target_owner,
                             package_definitions[target_owner][package_symbols[package]], package_symbols[package])
            if record['super_constructor'] is None:
                self._require(record['cpp_parent'] == name == 'UObject' and record['class_path'] == '/Script/CoreUObject.Object')
                parents[record['class_path']] = None
            else:
                parent = record['cpp_parent']
                self._require(parent in records)
                self._pointer_to(owner, record['super_constructor'], owners[parent],
                                 records[parent]['constructor_address'], symbols[parent])
                parents[record['class_path']] = records[parent]['class_path']
        self._require([name for name, parent in parents.items() if parent is None] == ['/Script/CoreUObject.Object'])
        for name in parents:
            visited, current = set(), name
            while current is not None:
                self._require(current in parents and current not in visited)
                visited.add(current)
                current = parents[current]
        self._parents = parents
        self._records = records
        self._used_inputs = {name: dict(inputs[name]) for name in source_bytes}

    @staticmethod
    def _require(condition):
        require(condition, 'lcer.native_ancestry_invalid')

    @staticmethod
    def _symbol(function):
        return '__Z' + str(len(function)) + function + '19ETypeConstructPhase'

    def _pointer_to(self, owner, pointer, target_owner, address, symbol):
        if pointer['kind'] == 'rebase':
            self._require(owner == target_owner and pointer['address'] == address)
            return
        self._require(pointer['kind'] == 'bind' and pointer['addend'] == 0 and pointer['symbol'] == symbol)
        candidates = [path for path, image in self._images.items()
                      if pointer['library'] in (path, image.install_name)]
        self._require(candidates == [target_owner])

    @property
    def class_parents(self):
        return dict(self._parents)

    def require_classes(self, class_paths):
        self._require(type(class_paths) in (list, tuple, set) and all(type(name) is str for name in class_paths))
        require(set(class_paths) <= set(self._parents), 'lcer.native_class_unresolved')
        return dict(self._parents)


class SourceInputForbidden(ValueError):
    """An independently located source edge; never a candidate verdict."""

    def __init__(self, path, function, callee, line, input_kind='platform'):
        super().__init__('lcer.source_input_forbidden')
        self.edge = {'path': path, 'function': function, 'input': input_kind,
                     'callee': callee, 'line': line}


PYTHON_FORBIDDEN_NAMES = frozenset(('eval', 'exec', '__import__', '__builtins__', 'compile',
                                  'globals', 'locals', 'vars'))
PYTHON_FORBIDDEN_ATTRIBUTES = frozenset(('__dict__', '__globals__', '__code__', '__closure__',
    '__getattribute__', '__subclasses__', '__import__', 'import_module', 'exec_module',
    'load_module', 'spec_from_file_location', 'spec_from_loader', 'run_module', 'run_path'))


def python_dependency_inventory(source_bytes, standard):
    """Enumerate lexical definitions/imports and refuse executable indirection.

    This is the Python dependency part of the source audit. It does not
    classify all value flows or accept the complete Python/C++ source audit.
    Candidate source is parsed as bytes, never imported by this function.
    """
    functions, imports, files = [], [], []
    forbidden_names = PYTHON_FORBIDDEN_NAMES
    forbidden_attributes = PYTHON_FORBIDDEN_ATTRIBUTES
    forbidden_modules = {'builtins', 'importlib', 'runpy'}

    class Visitor(ast.NodeVisitor):
        def __init__(self, path):
            self.path = path
            self.scope = []

        def fail(self, node, callee):
            raise SourceInputForbidden(self.path, '.'.join(self.scope) or '<module>',
                                       callee, node.lineno)

        def definition(self, node):
            name = node.name if hasattr(node, 'name') else '<lambda@%d:%d>' % (node.lineno, node.col_offset)
            self.scope.append(name)
            try:
                functions.append({'path': self.path, 'function': '.'.join(self.scope),
                                  'kind': type(node).__name__, 'line': node.lineno,
                                  'end_line': node.end_lineno})
                self.generic_visit(node)
            finally:
                self.scope.pop()

        visit_FunctionDef = definition
        visit_AsyncFunctionDef = definition
        visit_Lambda = definition

        def visit_ClassDef(self, node):
            self.scope.append(node.name)
            try:
                self.generic_visit(node)
            finally:
                self.scope.pop()

        def imported(self, node, module, symbol, alias):
            top = module.split('.')[0]
            if (top not in standard | LOCAL_MODULES or top in forbidden_modules
                    or (top in LOCAL_MODULES and module != top) or symbol == '*'):
                self.fail(node, module + ('.' + symbol if symbol else ''))
            imports.append({'path': self.path, 'function': '.'.join(self.scope) or '<module>',
                            'module': module, 'symbol': symbol, 'alias': alias,
                            'local_path': 'proof_kernel/' + top + '.py' if top in LOCAL_MODULES else None,
                            'line': node.lineno})

        def visit_Import(self, node):
            for item in node.names:
                self.imported(node, item.name, None, item.asname or item.name.split('.')[0])

        def visit_ImportFrom(self, node):
            if node.level != 0 or node.module is None:
                self.fail(node, '.' * node.level + (node.module or ''))
            for item in node.names:
                self.imported(node, node.module, item.name, item.asname or item.name)

        def visit_Name(self, node):
            # Reject obtaining an executable builtin too, so assigning it to
            # an alias or passing it through a helper cannot hide the edge.
            if isinstance(node.ctx, ast.Load) and node.id in forbidden_names:
                self.fail(node, node.id)

        def visit_Attribute(self, node):
            if node.attr in forbidden_attributes:
                self.fail(node, node.attr)
            self.generic_visit(node)

        def visit_Call(self, node):
            if (isinstance(node.func, ast.Name) and node.func.id == 'getattr'
                    and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant)
                    and node.args[1].value in forbidden_attributes | forbidden_names):
                self.fail(node, 'getattr.' + node.args[1].value)
            self.generic_visit(node)

    for name in sorted(LOCAL_MODULES):
        relative = 'proof_kernel/' + name + '.py'
        require(relative in source_bytes)
        raw = source_bytes[relative]
        require(type(raw) is bytes)
        tree = ast.parse(raw, filename=relative)
        Visitor(relative).visit(tree)
        files.append({'path': relative, 'sha256': digest(raw), 'size_bytes': len(raw)})
    require(all(row['local_path'] is None or row['local_path'] in source_bytes for row in imports))
    return {'files': files, 'functions': functions, 'imports': imports}


class BuildRuleSourceInventory:
    """Parse the candidate's restricted C# module-rule source without running it.

    This reader covers a single public ModuleRules constructor, calls, stores,
    qualified names, regular strings without escapes and inferred arrays.
    Unsupported declarations or syntax reject the entire inventory. Call and
    property semantics remain separate obligations; lexical coverage is not
    source-audit acceptance or a C# compiler result.
    """

    TOKEN = re.compile(r'(?P<space>[ \t\r\n]+)|(?P<line>//[^\r\n]*)|'
                       r'(?P<comment>/\*[\s\S]*?\*/)|(?P<string>"[^"\\\r\n]*")|'
                       r'(?P<word>[A-Za-z_][A-Za-z_0-9]*)|(?P<symbol>[{}()\[\].,:;=])')
    KEYWORDS = frozenset(('abstract as base bool break byte case catch char checked class const continue '
                          'decimal default delegate do double else enum event explicit extern false finally '
                          'fixed float for foreach goto if implicit in int interface internal is lock long '
                          'namespace new null object operator out override params private protected public '
                          'readonly ref return sbyte sealed short sizeof stackalloc static string struct '
                          'switch this throw true try typeof uint ulong unchecked unsafe ushort using '
                          'virtual void volatile while').split())

    def parse(self, path, raw):
        require(type(path) is str and path.endswith('.Build.cs') and type(raw) is bytes and len(raw) <= 65536,
                'lcer.build_rule_syntax_unclassified')
        try:
            text = raw.decode('ascii')
        except UnicodeError as error:
            raise ValueError('lcer.build_rule_syntax_unclassified') from error
        require(all(ord(c) >= 32 or c in '\t\r\n' for c in text), 'lcer.build_rule_syntax_unclassified')
        tokens, offset = [], 0
        while offset < len(text):
            match = self.TOKEN.match(text, offset)
            require(match is not None, 'lcer.build_rule_syntax_unclassified')
            if match.lastgroup not in ('space', 'line', 'comment'):
                tokens.append({'kind': match.lastgroup, 'text': match.group(), 'offset': offset,
                               'end_offset': match.end(),
                               'line': len(re.findall(r'\r\n|\r|\n', text[:offset])) + 1})
            offset = match.end()
        tokens.append({'kind': 'end', 'text': '', 'offset': len(raw), 'end_offset': len(raw),
                       'line': len(re.findall(r'\r\n|\r|\n', text)) + 1})
        position, calls, stores = [0], [], []

        def peek(value):
            return tokens[position[0]]['text'] == value

        def take(value=None):
            token = tokens[position[0]]
            require(token['kind'] != 'end' and (value is None or token['text'] == value),
                    'lcer.build_rule_syntax_unclassified')
            position[0] += 1
            return token

        def name():
            token = take()
            require(token['kind'] == 'word' and token['text'] not in self.KEYWORDS,
                    'lcer.build_rule_syntax_unclassified')
            return token

        def qualified():
            token = name()
            result = dict(token)
            while peek('.'):
                take('.')
                part = name()
                result['text'] += '.' + part['text']
                result['end_offset'] = part['end_offset']
            return result

        def expression(depth=0):
            require(depth < 32, 'lcer.build_rule_syntax_unclassified')
            token = tokens[position[0]]
            if token['kind'] == 'string':
                take()
                return {'kind': 'string', 'value': token['text'][1:-1], 'offset': token['offset'],
                        'end_offset': token['end_offset'], 'line': token['line']}
            if peek('new'):
                take('new'); take('['); take(']'); take('{')
                items = []
                while not peek('}'):
                    items.append(expression(depth + 1))
                    if not peek(','):
                        break
                    take(',')
                end = take('}')
                return {'kind': 'array', 'items': items, 'offset': token['offset'],
                        'end_offset': end['end_offset'], 'line': token['line']}
            target = qualified()
            result = {'kind': 'name', 'value': target['text'], 'offset': target['offset'],
                      'end_offset': target['end_offset'], 'line': target['line']}
            if peek('('):
                take('(')
                arguments = []
                while not peek(')'):
                    arguments.append(expression(depth + 1))
                    if not peek(','):
                        break
                    take(',')
                end = take(')')
                result.update(kind='call', callee=result.pop('value'), arguments=arguments,
                              end_offset=end['end_offset'])
                calls.append(result)
            return result

        take('using'); take('UnrealBuildTool'); take(';')
        take('public'); take('class')
        module = name()
        require(module['text'] == Path(path).name[:-len('.Build.cs')], 'lcer.build_rule_syntax_unclassified')
        take(':'); take('ModuleRules'); take('{')
        start = take('public')
        take(module['text']); take('('); take('ReadOnlyTargetRules')
        parameter = name()
        take(')'); take(':')
        base = take('base')
        take('('); take(parameter['text']); end = take(')')
        calls.append({'kind': 'base_constructor', 'callee': 'base', 'base_type': 'ModuleRules',
                      'arguments': [{'kind': 'name', 'value': parameter['text']}],
                      'offset': base['offset'], 'end_offset': end['end_offset'], 'line': base['line']})
        take('{')
        statements = []
        while not peek('}'):
            left = expression()
            if peek('='):
                require(left['kind'] == 'name', 'lcer.build_rule_syntax_unclassified')
                take('=')
                right = expression()
                operation = {'kind': 'store', 'target': left, 'value': right, 'line': left['line']}
                stores.append(operation)
            else:
                require(left['kind'] == 'call', 'lcer.build_rule_syntax_unclassified')
                operation = left
            take(';')
            statements.append(operation)
        end = take('}')
        take('}')
        require(tokens[position[0]]['kind'] == 'end', 'lcer.build_rule_syntax_unclassified')
        function = module['text'] + '.' + module['text']
        for operation in [*calls, *stores]:
            operation.update(path=path, function=function)
        return {'files': [{'path': path, 'sha256': digest(raw), 'size_bytes': len(raw)}],
                'functions': [{'path': path, 'function': function, 'kind': 'Constructor',
                               'line': start['line'], 'end_line': end['line'],
                               'parameters': [{'name': parameter['text'], 'type': 'ReadOnlyTargetRules'}],
                               'statements': statements}],
                'calls': calls, 'stores': stores, 'source_audit_complete': False}


class BuildRuleEffectAnalysis:
    """Source-level effects for the reviewed UE module-rule API subset.

    Hashes bind the engine bodies underlying these finite summaries. Candidate
    statements and argument origins still come from a complete parse. This
    neither executes a rule nor establishes installed-assembly equivalence.
    Unknown expressions and operations remain explicit policy obligations.
    """

    ENGINE_SOURCES = {
        'ModuleRules.cs': 'ab0dba9138c9bca4ab4663138fd2fe7924ebb6b96357be809602bf13e882329d',
        'CppCompileWarnings.cs': 'efe72641da4ea040eff104f1a5cf055dec3518d015c8c3935d0fd9c48b3adec3',
        'ReadOnlyTargetRules.cs': '179b8136e312702bd1ba779db2b35aea702dbe7a8efcf5738b0623c9edab112c',
        'TargetRules.cs': 'e135c4552ce0949516a7a699d2a26cd0424b52d05cd13a7c0289beeccab44beb',
        'BuildSystemContext.cs': '97177aa4d73efc4e30974278be1b5b8321859ab8725e7f371dea422d57eca078',
        'ModuleRules.Obsolete.cs': '54e5156515320755ec9987ee8c1248696929d6773a49f26eeeb6f1b8d354eadb',
        'ReadOnlyCppCompileWarnings.cs': 'e000709bf9d86dc44e773ab9a2235f15e5c3c3a9be64e13f764e17af3d87f750',
        'RulesAssembly.cs': '43ee099ab650d9602bcd1925a25915a61ac9b7e17999213cc05e351162790c35',
    }
    TARGET_TYPE = 'UnrealBuildTool.ReadOnlyTargetRules'
    PCH_TYPE = 'UnrealBuildTool.ModuleRules.PCHUsageMode'
    BASE = 'UnrealBuildTool.ModuleRules.ModuleRules(UnrealBuildTool.ReadOnlyTargetRules)'
    ADD_RANGE = 'System.Collections.Generic.List<System.String>.AddRange(System.Collections.Generic.IEnumerable<System.String>)'
    THIRD_PARTY = 'UnrealBuildTool.ModuleRules.AddEngineThirdPartyPrivateStaticDependencies(UnrealBuildTool.ReadOnlyTargetRules,System.String[])'
    PCH_SETTER = 'UnrealBuildTool.ModuleRules.PCHUsage.set(UnrealBuildTool.ModuleRules.PCHUsageMode)'

    def analyze(self, path, raw, engine_sources):
        require(type(engine_sources) is dict and set(engine_sources) == set(self.ENGINE_SOURCES),
                'lcer.build_rule_api_identity_mismatch')
        require(all(type(value) is bytes and digest(value) == self.ENGINE_SOURCES[name]
                    for name, value in engine_sources.items()), 'lcer.build_rule_api_identity_mismatch')
        inventory = BuildRuleSourceInventory().parse(path, raw)
        function = inventory['functions'][0]
        parameter = function['parameters'][0]['name']
        unknown, effects, edges = [], [], []

        def unresolved(node, callee, reason):
            row = {'path': path, 'function': function['function'], 'callee': callee,
                   'line': node.get('line', function['line']), 'reason': reason}
            if row not in unknown:
                unknown.append(row)

        def expression(node):
            kind = node['kind']
            if kind == 'string':
                return {'type': 'System.String', 'value': node['value'], 'origins': []}
            if kind == 'array':
                items = [expression(item) for item in node['items']]
                return {'type': 'System.String[]' if items and all(item['type'] == 'System.String' for item in items) else None,
                        'items': items, 'origins': sorted({origin for item in items for origin in item['origins']})}
            if kind == 'name' and node['value'] == parameter:
                return {'type': self.TARGET_TYPE, 'reference': 'target', 'origins': ['platform:target']}
            if kind == 'name' and node['value'] == 'PCHUsageMode.UseExplicitOrSharedPCHs':
                return {'type': self.PCH_TYPE, 'value': node['value'], 'origins': []}
            if kind == 'call':
                arguments = [expression(arg) for arg in node['arguments']]
                unresolved(node, node['callee'], 'call_binding_unclassified')
                return {'type': None, 'callee': node['callee'], 'arguments': arguments,
                        'origins': sorted({'unclassified:' + node['callee']} |
                                          {origin for arg in arguments for origin in arg['origins']})}
            unresolved(node, node['value'], 'value_binding_unclassified')
            return {'type': None, 'value': node['value'], 'origins': ['unclassified:' + node['value']]}

        base = inventory['calls'][0]
        require(base['kind'] == 'base_constructor', 'lcer.build_rule_syntax_unclassified')
        effects.append({'path': path, 'function': function['function'], 'line': base['line'],
                        'signature': self.BASE, 'source': {'file': 'ModuleRules.cs', 'line': 1581},
                        'arguments': [expression(arg) for arg in base['arguments']],
                        'operation': 'construct_base',
                        'operations': [
                            {'operation': 'initialize_containers',
                             'targets': ['receiver.PublicDependencyModuleNames', 'receiver.PrivateDependencyModuleNames',
                                         'receiver.RuntimeDependencies', 'receiver.AdditionalPropertiesForReceipt'],
                             'elements': [], 'container_identity': 'distinct'},
                            {'operation': 'conditional_clone', 'target': 'receiver.StaticAnalyzerDisabledCheckers',
                             'source': 'ModuleRules.DefaultStaticAnalyzerDisabledCheckers',
                             'guard': {'op': 'not_equal', 'left': 'target.StaticAnalyzer', 'right': 'StaticAnalyzer.None'},
                             'container_identity': 'fresh', 'elements': 'current_string_references'},
                            {'operation': 'store_reference', 'target': 'receiver.Target', 'source': 'target'},
                            {'operation': 'construct_warnings',
                             'signature': 'UnrealBuildTool.CppCompileWarnings.CppCompileWarnings(UnrealBuildTool.ModuleRules,Microsoft.Extensions.Logging.ILogger?)',
                             'source': {'file': 'CppCompileWarnings.cs', 'line': 1435},
                             'retained_aliases': {'context.module': 'receiver', 'provider.module': 'receiver',
                                                  'context.target': None, 'parent_warnings': 'target.CppCompileWarningSettings',
                                                  'logger': 'target.Logger'},
                             'invoked_callbacks': [], 'applies_defaults': False}],
                        'origins': ['platform:target', 'platform:ModuleRules.DefaultStaticAnalyzerDisabledCheckers'],
                        'failure_effect': 'construction_can_fail_after_prior_writes'})

        for statement in function['statements']:
            if statement['kind'] == 'store':
                value = expression(statement['value'])
                target = statement['target']['value']
                effect = {'operation': 'store', 'target': target, 'value': value, 'origins': value['origins']}
                if target == 'PCHUsage' and value['type'] == self.PCH_TYPE:
                    effect.update(signature=self.PCH_SETTER, target='receiver.PCHUsagePrivate',
                                  source={'file': 'ModuleRules.cs', 'line': 845})
                else:
                    unresolved(statement, target, 'store_binding_unclassified')
            else:
                arguments = [expression(arg) for arg in statement['arguments']]
                callee = statement['callee']
                origins = sorted({origin for arg in arguments for origin in arg['origins']})
                effect = {'operation': 'call', 'callee': callee, 'arguments': arguments, 'origins': origins}
                if callee in ('PublicDependencyModuleNames.AddRange', 'PrivateDependencyModuleNames.AddRange'):
                    if len(arguments) == 1 and arguments[0]['type'] == 'System.String[]':
                        effect.update(signature=self.ADD_RANGE, operation='append',
                                      receiver='receiver.' + callee.split('.')[0],
                                      elements=arguments[0]['items'], element_transfer='ordered_reference_copy',
                                      argument_container_retained=False, guard=None)
                    else:
                        unresolved(statement, callee, 'call_argument_type_unclassified')
                elif callee == 'AddEngineThirdPartyPrivateStaticDependencies':
                    if (len(arguments) >= 2 and arguments[0]['type'] == self.TARGET_TYPE and
                            (all(arg['type'] == 'System.String' for arg in arguments[1:]) or
                             (len(arguments) == 2 and arguments[1]['type'] == 'System.String[]'))):
                        elements = arguments[1]['items'] if arguments[1]['type'] == 'System.String[]' else arguments[1:]
                        effect.update(signature=self.THIRD_PARTY, source={'file': 'ModuleRules.cs', 'line': 1601},
                                      operation='append', receiver='receiver.PrivateDependencyModuleNames',
                                      elements=elements, element_transfer='ordered_reference_copy',
                                      params_form='array' if arguments[1]['type'] == 'System.String[]' else 'expanded',
                                      argument_container_retained=False,
                                      guard={'op': 'short_circuit_or',
                                             'left': {'op': 'not', 'value': 'receiver.bUsePrecompiled'},
                                             'right': {'op': 'equal', 'left': 'target.LinkType', 'right': 'TargetLinkType.Monolithic'}},
                                      origins=sorted(set(origins) | {'platform:receiver.bUsePrecompiled'}))
                    else:
                        unresolved(statement, callee, 'call_argument_type_unclassified')
                else:
                    unresolved(statement, callee, 'call_binding_unclassified')
            effect.update(path=path, function=function['function'], line=statement['line'])
            effects.append(effect)

        for effect in effects:
            if 'signature' in effect and any(origin.startswith('platform:') for origin in effect['origins']):
                edge = {'path': path, 'function': function['function'], 'input': 'platform',
                        'callee': effect['signature'], 'consequence': 'provenance'}
                if edge not in edges:
                    edges.append(edge)
        return {'files': inventory['files'], 'functions': inventory['functions'], 'effects': effects,
                'source_edges': edges, 'unclassified': unknown,
                'engine_source_hashes': dict(self.ENGINE_SOURCES),
                'identity_kind': 'source_signatures',
                'external_obligations': [
                    'installed_assembly_source_correspondence',
                    'framework_collection_and_allocation_effects',
                    'actual_rules_type_and_preinitialized_receiver',
                    'upstream_target_configuration_and_later_dependency_resolution',
                    'deferred_warning_context_logger_and_reflection_consumers'],
                'source_audit_complete': False}


class ClangSourceInventory:
    """Read compiler cursors without importing candidate acquisition code.

    A cursor inventory is evidence for subsequent flow analysis. Parsing and
    input hashes alone never establish source-audit or release acceptance.
    """

    LIBRARY = '/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/libclang.dylib'

    def __init__(self):
        class String(ctypes.Structure):
            _fields_ = [('data', ctypes.c_void_p), ('private_flags', ctypes.c_uint)]

        class Cursor(ctypes.Structure):
            _fields_ = [('kind', ctypes.c_uint), ('xdata', ctypes.c_int), ('data', ctypes.c_void_p * 3)]

        class Location(ctypes.Structure):
            _fields_ = [('ptr_data', ctypes.c_void_p * 2), ('int_data', ctypes.c_uint)]

        class Range(ctypes.Structure):
            _fields_ = [('ptr_data', ctypes.c_void_p * 2), ('begin_int_data', ctypes.c_uint), ('end_int_data', ctypes.c_uint)]

        class Type(ctypes.Structure):
            _fields_ = [('kind', ctypes.c_uint), ('data', ctypes.c_void_p * 2)]

        self.library_raw = Path(self.LIBRARY).read_bytes()
        self.library = ctypes.CDLL(self.LIBRARY)
        self.Cursor = Cursor
        self.Callback = ctypes.CFUNCTYPE(ctypes.c_uint, Cursor, Cursor, ctypes.c_void_p)
        self.FieldCallback = ctypes.CFUNCTYPE(ctypes.c_uint, Cursor, ctypes.c_void_p)
        self.api = {}

        def bind(name, result, arguments, function):
            # The call site supplies the exact native symbol after evaluating
            # its result/argument types. Keep registration order unchanged.
            function.restype, function.argtypes = result, arguments
            self.api[name] = function

        bind('createIndex', ctypes.c_void_p, [ctypes.c_int, ctypes.c_int], self.library.clang_createIndex)
        bind('disposeIndex', None, [ctypes.c_void_p], self.library.clang_disposeIndex)
        bind('parseTranslationUnit2FullArgv', ctypes.c_int,
             [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p), ctypes.c_int,
              ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)], self.library.clang_parseTranslationUnit2FullArgv)
        bind('disposeTranslationUnit', None, [ctypes.c_void_p], self.library.clang_disposeTranslationUnit)
        bind('getTranslationUnitCursor', Cursor, [ctypes.c_void_p], self.library.clang_getTranslationUnitCursor)
        bind('visitChildren', ctypes.c_uint, [Cursor, self.Callback, ctypes.c_void_p], self.library.clang_visitChildren)
        bind('getCursorSpelling', String, [Cursor], self.library.clang_getCursorSpelling)
        bind('getCursorUSR', String, [Cursor], self.library.clang_getCursorUSR)
        bind('getCursorKindSpelling', String, [ctypes.c_uint], self.library.clang_getCursorKindSpelling)
        bind('getCursorLocation', Location, [Cursor], self.library.clang_getCursorLocation)
        bind('getCursorExtent', Range, [Cursor], self.library.clang_getCursorExtent)
        bind('getRangeStart', Location, [Range], self.library.clang_getRangeStart)
        bind('getRangeEnd', Location, [Range], self.library.clang_getRangeEnd)
        bind('getCursorType', Type, [Cursor], self.library.clang_getCursorType)
        bind('getCursorResultType', Type, [Cursor], self.library.clang_getCursorResultType)
        bind('getTypeSpelling', String, [Type], self.library.clang_getTypeSpelling)
        bind('getCanonicalType', Type, [Type], self.library.clang_getCanonicalType)
        bind('getTypeKindSpelling', String, [ctypes.c_uint], self.library.clang_getTypeKindSpelling)
        bind('getTypeDeclaration', Cursor, [Type], self.library.clang_getTypeDeclaration)
        bind('Type_visitFields', ctypes.c_uint, [Type, self.FieldCallback, ctypes.c_void_p], self.library.clang_Type_visitFields)
        bind('Cursor_getOffsetOfField', ctypes.c_longlong, [Cursor], self.library.clang_Cursor_getOffsetOfField)
        bind('getCursorReferenced', Cursor, [Cursor], self.library.clang_getCursorReferenced)
        bind('Cursor_getVarDeclInitializer', Cursor, [Cursor], self.library.clang_Cursor_getVarDeclInitializer)
        bind('Cursor_hasVarDeclGlobalStorage', ctypes.c_int, [Cursor], self.library.clang_Cursor_hasVarDeclGlobalStorage)
        bind('getCursorSemanticParent', Cursor, [Cursor], self.library.clang_getCursorSemanticParent)
        bind('Cursor_isNull', ctypes.c_int, [Cursor], self.library.clang_Cursor_isNull)
        bind('hashCursor', ctypes.c_uint, [Cursor], self.library.clang_hashCursor)
        bind('equalCursors', ctypes.c_uint, [Cursor, Cursor], self.library.clang_equalCursors)
        bind('isCursorDefinition', ctypes.c_uint, [Cursor], self.library.clang_isCursorDefinition)
        bind('Cursor_isDynamicCall', ctypes.c_int, [Cursor], self.library.clang_Cursor_isDynamicCall)
        bind('Cursor_getNumArguments', ctypes.c_int, [Cursor], self.library.clang_Cursor_getNumArguments)
        bind('Cursor_getArgument', Cursor, [Cursor, ctypes.c_uint], self.library.clang_Cursor_getArgument)
        bind('getCursorBinaryOperatorKind', ctypes.c_uint, [Cursor], self.library.clang_getCursorBinaryOperatorKind)
        bind('getBinaryOperatorKindSpelling', String, [ctypes.c_uint], self.library.clang_getBinaryOperatorKindSpelling)
        bind('getCursorUnaryOperatorKind', ctypes.c_uint, [Cursor], self.library.clang_getCursorUnaryOperatorKind)
        bind('getUnaryOperatorKindSpelling', String, [ctypes.c_uint], self.library.clang_getUnaryOperatorKindSpelling)
        bind('CXXMethod_isStatic', ctypes.c_uint, [Cursor], self.library.clang_CXXMethod_isStatic)
        bind('CXXMethod_isConst', ctypes.c_uint, [Cursor], self.library.clang_CXXMethod_isConst)
        bind('CXXMethod_isVirtual', ctypes.c_uint, [Cursor], self.library.clang_CXXMethod_isVirtual)
        place_args = [Location, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint),
                      ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
        bind('getExpansionLocation', None, place_args, self.library.clang_getExpansionLocation)
        bind('getSpellingLocation', None, place_args, self.library.clang_getSpellingLocation)
        bind('getFileName', String, [ctypes.c_void_p], self.library.clang_getFileName)
        bind('getCString', ctypes.c_char_p, [String], self.library.clang_getCString)
        bind('disposeString', None, [String], self.library.clang_disposeString)
        bind('getNumDiagnostics', ctypes.c_uint, [ctypes.c_void_p], self.library.clang_getNumDiagnostics)
        bind('getDiagnostic', ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_uint], self.library.clang_getDiagnostic)
        bind('getDiagnosticSeverity', ctypes.c_uint, [ctypes.c_void_p], self.library.clang_getDiagnosticSeverity)
        bind('getDiagnosticSpelling', String, [ctypes.c_void_p], self.library.clang_getDiagnosticSpelling)
        bind('disposeDiagnostic', None, [ctypes.c_void_p], self.library.clang_disposeDiagnostic)

    def text(self, value):
        try:
            raw = self.api['getCString'](value)
            return raw.decode('utf-8', 'strict') if raw else ''
        finally:
            self.api['disposeString'](value)

    def location(self, value, spelling=False):
        file = ctypes.c_void_p()
        line, column, offset = ctypes.c_uint(), ctypes.c_uint(), ctypes.c_uint()
        self.api['getSpellingLocation' if spelling else 'getExpansionLocation'](
            value, ctypes.byref(file), ctypes.byref(line), ctypes.byref(column), ctypes.byref(offset))
        return {'path': self.text(self.api['getFileName'](file)) if file else None,
                'line': line.value, 'column': column.value, 'offset': offset.value}

    def qualified(self, cursor):
        names = []
        for _ in range(64):
            if self.api['Cursor_isNull'](cursor) or self.text(self.api['getCursorKindSpelling'](cursor.kind)) == 'TranslationUnit':
                return '::'.join(reversed(names))
            name = self.text(self.api['getCursorSpelling'](cursor))
            if name:
                names.append(name)
            cursor = self.api['getCursorSemanticParent'](cursor)
        raise ValueError('lcer.source_cursor_budget_exceeded')

    def describe(self, cursor):
        extent = self.api['getCursorExtent'](cursor)
        value_type = self.api['getCursorType'](cursor)
        record = {'kind': self.text(self.api['getCursorKindSpelling'](cursor.kind)),
                'usr': self.text(self.api['getCursorUSR'](cursor)),
                'name': self.text(self.api['getCursorSpelling'](cursor)),
                'type': self.text(self.api['getTypeSpelling'](value_type)),
                'type_kind': self.text(self.api['getTypeKindSpelling'](self.api['getCanonicalType'](value_type).kind)),
                'start': self.location(self.api['getRangeStart'](extent)),
                'end': self.location(self.api['getRangeEnd'](extent))}
        if record['kind'] == 'VarDecl':
            answer = self.api['Cursor_hasVarDeclGlobalStorage'](cursor)
            require(answer in (0, 1), 'lcer.source_inventory_invalid')
            record['global_storage'] = bool(answer)
        if record['kind'] in ('FunctionDecl', 'CXXMethod', 'CXXConstructor', 'CXXDestructor',
                              'FunctionTemplate', 'CXXConversion'):
            result_type = self.api['getCursorResultType'](cursor)
            record['result_type'] = self.text(self.api['getTypeSpelling'](result_type))
            record['result_type_kind'] = self.text(self.api['getTypeKindSpelling'](
                self.api['getCanonicalType'](result_type).kind))
        return record

    def children(self, cursor):
        children, errors = [], []

        @self.Callback
        def collect(child, parent, _):
            if len(children) >= 200000:
                errors.append('cursor budget exceeded')
                return 0
            children.append(child)
            return 1

        self.api['visitChildren'](cursor, collect, None)
        require(not errors, 'lcer.source_cursor_budget_exceeded')
        return children

    def lambda_closure(self, cursor):
        value_type = self.api['getCursorType'](cursor)
        declaration = self.api['getTypeDeclaration'](value_type)
        operators = [child for child in self.children(declaration)
                     if self.text(self.api['getCursorKindSpelling'](child.kind)) == 'CXXMethod'
                     and self.text(self.api['getCursorSpelling'](child)) == 'operator()']
        record = self.describe(declaration)
        record['fields'] = []
        errors = []

        @self.FieldCallback
        def field(child, _):
            try:
                require(len(record['fields']) < 200000, 'lcer.source_cursor_budget_exceeded')
                item = self.describe(child)
                item.update(ordinal=len(record['fields']), offset_bits=self.api['Cursor_getOffsetOfField'](child),
                            location=self.location(self.api['getCursorLocation'](child)))
                record['fields'].append(item)
                return 1
            except BaseException as error:
                errors.append(type(error).__name__ + ': ' + str(error))
                return 0

        self.api['Type_visitFields'](value_type, field, None)
        require(not errors, 'lcer.source_closure_fields_invalid')
        references = [child for child in self.children(cursor)
                      if self.text(self.api['getCursorKindSpelling'](child.kind)) == 'VariableRef']
        for item in record['fields']:
            matching = [child for child in references
                        if self.location(self.api['getCursorLocation'](child)) == item['location']]
            if len(matching) == 1:
                declaration = self.api['getCursorReferenced'](matching[0])
                item['capture_reference'] = {
                    'declaration': self.describe(declaration),
                    'declaration_location': self.location(self.api['getCursorLocation'](declaration)),
                    'binding_basis': 'unique_explicit_capture_location'}
        record['operator_usrs'] = [self.text(self.api['getCursorUSR'](method)) for method in operators]
        return record, declaration, operators

    def lambda_creation_children(self, cursor):
        # CIndex visits an init-capture's initializer children, omitting its
        # root expression. The capture reference identifies the actual VarDecl
        # and getVarDeclInitializer supplies that missing root. Ordinary capture
        # references point to earlier declarations and must not replay them.
        children = self.children(cursor)
        declarations, covered = [], []
        for child in children:
            if self.text(self.api['getCursorKindSpelling'](child.kind)) != 'VariableRef':
                continue
            declaration = self.api['getCursorReferenced'](child)
            if (self.text(self.api['getCursorKindSpelling'](declaration.kind)) != 'VarDecl' or
                    self.location(self.api['getCursorLocation'](declaration), True) !=
                    self.location(self.api['getCursorLocation'](child), True)):
                continue
            initializer = self.api['Cursor_getVarDeclInitializer'](declaration)
            if self.api['Cursor_isNull'](initializer):
                continue
            declarations.append(declaration)
            covered.extend([initializer, *self.children(initializer)])
        retained = [child for child in children
                    if self.text(self.api['getCursorKindSpelling'](child.kind)) not in ('ParmDecl', 'CompoundStmt')
                    and not any(self.api['equalCursors'](child, item) for item in covered)]
        return retained, declarations

    def parse(self, source_path, source_paths, argv, api_source_paths=()):
        path = Path(source_path).absolute()
        source_paths = [Path(name).absolute() for name in source_paths]
        api_source_paths = [Path(name).absolute() for name in api_source_paths]
        require(path in source_paths and len(set(source_paths)) == len(source_paths), 'lcer.source_inventory_invalid')
        require(len(set(api_source_paths)) == len(api_source_paths), 'lcer.source_inventory_invalid')
        require(type(argv) is list and 1 <= len(argv) <= 10000 and
                all(type(value) is str and value and '\0' not in value for value in argv), 'lcer.source_inventory_invalid')
        for value in argv:
            if (value.startswith(('@', '-fplugin=', '-fpass-plugin=')) or
                    value in ('-load', '-plugin', '-add-plugin')):
                raise SourceInputForbidden(str(path), '<compiler>', value, 0)

        def snapshot(paths):
            files = {}
            for name in paths:
                require(name == name.resolve() and name.is_file() and
                        not any(item.is_symlink() for item in [name, *name.parents]), 'lcer.source_inventory_invalid')
                files[str(name)] = digest(name.read_bytes())
            return files

        before = snapshot(source_paths)
        api_before = snapshot(api_source_paths)
        api = self.api
        record = {'source': str(path), 'argv': list(argv), 'source_hashes': before,
                  'libclang_path': self.LIBRARY, 'libclang_sha256': digest(self.library_raw),
                  'nodes': [], 'declarations': [], 'references': [], 'diagnostics': [],
                  'source_audit_complete': False, 'api_source_hashes': api_before}
        index = api['createIndex'](1, 0)
        require(bool(index), 'lcer.source_compiler_unavailable')
        unit = ctypes.c_void_p()
        parents, functions, visitor_errors = [], [], []
        cursor_objects, argument_objects = {}, []
        count = [0]
        try:
            vector = (ctypes.c_char_p * len(argv))(*(value.encode('utf-8') for value in argv))
            record['parse_returncode'] = api['parseTranslationUnit2FullArgv'](
                index, str(path).encode('utf-8'), vector, len(argv), None, 0, 0, ctypes.byref(unit))
            if unit:
                for number in range(api['getNumDiagnostics'](unit)):
                    diagnostic = api['getDiagnostic'](unit, number)
                    try:
                        record['diagnostics'].append({'severity': api['getDiagnosticSeverity'](diagnostic),
                                                      'message': self.text(api['getDiagnosticSpelling'](diagnostic))})
                    finally:
                        api['disposeDiagnostic'](diagnostic)

                @self.Callback
                def visit(cursor, parent, _):
                    try:
                        count[0] += 1
                        require(count[0] <= 200000, 'lcer.source_cursor_budget_exceeded')
                        place = self.location(api['getCursorLocation'](cursor))
                        if place['path'] not in before:
                            return 1
                        node = self.describe(cursor)
                        kind, number = node['kind'], len(record['nodes'])
                        is_function = kind in ('FunctionDecl', 'CXXMethod', 'CXXConstructor', 'CXXDestructor',
                                               'FunctionTemplate', 'CXXConversion')
                        node.update(id=number, parent=parents[-1] if parents else None,
                                    function=functions[-1] if functions else '<translation-unit>', location=place,
                                    definition=bool(api['isCursorDefinition'](cursor)), qualified=self.qualified(cursor),
                                    arguments=[], binary_operator=None, unary_operator=None)
                        closure, operators = None, []
                        if kind == 'LambdaExpr':
                            node['lambda_closure'], closure, operators = self.lambda_closure(cursor)
                            node['lambda_operator_node'] = None
                        if kind in ('BinaryOperator', 'CompoundAssignOperator'):
                            node['binary_operator'] = self.text(api['getBinaryOperatorKindSpelling'](api['getCursorBinaryOperatorKind'](cursor)))
                        if kind == 'UnaryOperator':
                            node['unary_operator'] = self.text(api['getUnaryOperatorKindSpelling'](api['getCursorUnaryOperatorKind'](cursor)))
                        if kind == 'CXXMethod':
                            node['method_properties'] = {suffix.lower(): bool(api['CXXMethod_is' + suffix](cursor))
                                                         for suffix in ('Static', 'Const', 'Virtual')}
                        for argument in range(max(0, api['Cursor_getNumArguments'](cursor))):
                            argument_cursor = api['Cursor_getArgument'](cursor, argument)
                            item = self.describe(argument_cursor)
                            item['index'] = argument
                            argument_objects.append((item, argument_cursor, number))
                            node['arguments'].append(item)
                        record['nodes'].append(node)
                        cursor_objects.setdefault(api['hashCursor'](cursor), []).append((cursor, number))
                        if is_function or kind in ('ClassDecl', 'StructDecl', 'LambdaExpr'):
                            record['declarations'].append({'node': number, 'kind': kind, 'name': node['qualified'],
                                                           'usr': node['usr'], 'definition': node['definition'],
                                                           'expansion': place,
                                                           'spelling': self.location(api['getCursorLocation'](cursor), True)})
                        if kind in ('CallExpr', 'DeclRefExpr', 'MemberRefExpr', 'VariableRef', 'C++ base class specifier', 'LambdaExpr', 'ObjCMessageExpr'):
                            target = api['getCursorReferenced'](cursor)
                            reference = {'node': number, 'kind': kind, 'name': node['name'],
                                                         'function': node['function'], 'location': place,
                                                         'target': self.qualified(target), 'target_usr': self.text(api['getCursorUSR'](target)),
                                                         'target_kind': self.text(api['getCursorKindSpelling'](target.kind)),
                                                         'target_type': self.text(api['getTypeSpelling'](api['getCursorType'](target))),
                                                         'target_location': self.location(api['getCursorLocation'](target), True),
                                                         'dynamic_call': bool(api['Cursor_isDynamicCall'](cursor))}
                            if kind == 'CallExpr':
                                parameter_count = api['Cursor_getNumArguments'](target)
                                reference['target_parameters'] = ([self.describe(api['Cursor_getArgument'](target, i))
                                                                   for i in range(parameter_count)]
                                                                  if parameter_count >= 0 else None)
                                if reference['target_kind'] in ('CXXMethod', 'CXXConversion'):
                                    reference['target_method_properties'] = {
                                        suffix.lower(): bool(api['CXXMethod_is' + suffix](target))
                                        for suffix in ('Static', 'Const', 'Virtual')}
                            record['references'].append(reference)
                        if is_function:
                            functions.append(node['qualified'])
                        parents.append(number)
                        try:
                            if kind == 'LambdaExpr' and len(operators) == 1:
                                # Preserve capture initialization. Traverse the
                                # real operator's parameters/body exactly once.
                                # CIndex gives different parent-context cursors
                                # for the original LambdaExpr body.
                                children, initializers = self.lambda_creation_children(cursor)
                                for child in children:
                                    visit(child, cursor, None)
                                node['lambda_initializer_nodes'] = []
                                for declaration in initializers:
                                    node['lambda_initializer_nodes'].append(len(record['nodes']))
                                    visit(declaration, cursor, None)
                                node['lambda_operator_node'] = len(record['nodes'])
                                visit(operators[0], closure, None)
                            else:
                                api['visitChildren'](cursor, visit, None)
                        finally:
                            parents.pop()
                            if is_function:
                                functions.pop()
                        return 1
                    except BaseException as error:
                        visitor_errors.append(type(error).__name__ + ': ' + str(error))
                        return 0

                api['visitChildren'](api['getTranslationUnitCursor'](unit), visit, None)
                # Resolve while the TU owns live cursors. Hashes are only an
                # index: libclang equality establishes every recorded match.
                for item, argument_cursor, owner in argument_objects:
                    item['cursor_nodes'] = [number for candidate, number in
                                            cursor_objects.get(api['hashCursor'](argument_cursor), ())
                                            if api['equalCursors'](candidate, argument_cursor)]
                    item['identity_basis'] = 'cursor_equality'
                    if not item['cursor_nodes'] and item['kind'] == 'DeclRefExpr':
                        # libclang can attach a different parent context to an
                        # argument reference in a variable initializer. Bind
                        # only a direct child with the same exact source span,
                        # type and equivalent referenced declaration.
                        declared = api['getCursorReferenced'](argument_cursor)
                        item['identity_basis'] = 'direct_reference_declaration'
                        for bucket in cursor_objects.values():
                            for candidate, number in bucket:
                                node = record['nodes'][number]
                                if (node['parent'] == owner and node['kind'] == 'DeclRefExpr' and
                                        node['start'] == item['start'] and node['end'] == item['end'] and
                                        node['type'] == item['type'] and not api['Cursor_isNull'](declared) and
                                        api['equalCursors'](declared, api['getCursorReferenced'](candidate))):
                                    item['cursor_nodes'].append(number)
                    if (not item['cursor_nodes'] and record['nodes'][owner]['kind'] == 'CallExpr' and
                            not api['Cursor_isNull'](argument_cursor)):
                        # Macro expansions can give getArgument an expression
                        # cursor unequal to every ordinary traversal cursor.
                        # Retain its own compiler subtree under this exact
                        # call/index. Never infer equality from a source range.
                        number = len(record['nodes'])
                        parents.append(owner)
                        functions.append(record['nodes'][owner]['function'])
                        try:
                            visit(argument_cursor, argument_cursor, None)
                        finally:
                            functions.pop()
                            parents.pop()
                        if len(record['nodes']) > number and record['nodes'][number]['parent'] == owner:
                            item['cursor_nodes'] = [number]
                            item['identity_basis'] = 'compiler_argument_subtree'
                            record['nodes'][number]['argument_owner'] = {'call': owner, 'index': item['index']}
        finally:
            if unit:
                api['disposeTranslationUnit'](unit)
            api['disposeIndex'](index)
        record['source_snapshot_unchanged'] = snapshot(source_paths) == before
        record['api_source_snapshot_unchanged'] = snapshot(api_source_paths) == api_before
        record['library_snapshot_unchanged'] = Path(self.LIBRARY).read_bytes() == self.library_raw
        record['visitor_errors'] = visitor_errors
        record['cursor_count'] = count[0]
        return record


class CppStringEffects:
    """Finite source effects for exact installed FString/view specializations.

    Value transfer is executable graph work. Memory lifetime and correspondence
    with the compiler artifacts remain separate obligations.
    """

    ROOT = '/Users/Shared/Epic Games/UE_5.8/Engine/Source/Runtime/Core/'
    SOURCE_HASHES = {
        'Private/Containers/String.cpp': '2cda0619668b8ce0b917f5777067f5a846f7b6114fc3b3682a1379397131b777',
        'Private/Containers/String.cpp.inl': 'd74629ae1e64faef6a5c78385d362025c37389d70c0d37a3f9c90b83fc7c4313',
        'Public/Apple/ApplePlatformString.h': 'ef49e016d30a0a9ee31a5e8db7334ad61c49e7f2bf5f634d2d65c81dd3c5ea78',
        'Public/Containers/Array.h': 'a5c173f3048e387efee4d2d43c52ba43811c9a5c6916c7892b72a817a72e5109',
        'Public/Containers/ContainerAllocationPolicies.h': '75383d5794aac3e62fd8f479575e1a1b89ad805708a17e300e31fc1f81518362',
        'Public/Containers/StringConv.h': 'd31bf3e39ff6f03665001e5d16b102002dfe3323b2463495addd1b0556369cf6',
        'Public/Containers/StringView.h': '366d0a7e3309de6154bcf9e82ce20c5c70065744e6bdfeb2536f8f770609585d',
        'Public/Containers/UnrealString.h': '62540da6528528a2d544918a18a223fda750f9c8b5cff204232847428b3a143a',
        'Public/Containers/UnrealString.h.inl': 'c2e41cf83e628a9657b03b4df591238f8f329f8242fb6448e02d791e6bf8ebe5',
        'Public/GenericPlatform/GenericPlatformString.h': '37fe32ef1068bdd33567a8b7b6738183c3bad304fd40be6dbbfb2b1c5afa522a',
        'Public/GenericPlatform/GenericWidePlatformString.h': '31b5c740f19783e8ddffdbb98399b3a03f682305375d2c3117ed45cf176fe68a',
        'Public/Misc/CString.h': '62c711bcc838bcf297971cb5d2c8951a905c9ec69171bf2e7eb51b631255dc20',
        'Public/Templates/MemoryOps.h': '87f99a1512f812dea8fce8bd96e3c50fbde89ed4282fe5d016ee2a8f63297cd3',
        'Public/Templates/TypeCompatibleBytes.h': 'b305024e6d2affd926810f039090135492509e114c7d8c79b8519a1b555999b3',
        'Public/Templates/UnrealTemplate.h': '2d5b53189bb5b00e50d783b0984e8c9ecfe3d01b3b47724d9f6eac99de90fbd7',
        'Public/Traits/IsCharEncodingCompatibleWith.h': '843f3267e91ed96d2bdaac8161c0f9562fc995ea61739e1d4021aed11e1f1d20',
        'Public/Traits/IsCharEncodingSimplyConvertibleTo.h': '4b33f533a9756957150c78da245f678c64f93c375a0124ed7b686b8e6e536759',
    }
    TARGETS = {
        'c:@S@FString@F@Len#1': {'id': 'STR01', 'kind': 'CXXMethod', 'type': 'int32 () const', 'location': {'column': 42, 'line': 932, 'offset': 38564, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'length', 'arity': 0},
        'c:@S@FString@F@operator*#1': {'id': 'STR02', 'kind': 'CXXMethod', 'type': 'const ElementType *() const', 'location': {'column': 55, 'line': 356, 'offset': 17068, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'borrow_buffer', 'arity': 0},
        'c:@S@FString@F@FString#': {'id': 'STR03', 'kind': 'CXXConstructor', 'type': 'void () noexcept(false)', 'location': {'column': 16, 'line': 80, 'offset': 3772, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'empty', 'arity': 0},
        'c:@S@FString@F@operator+=<#$@S@FString>#&&S0_#': {'id': 'STR04', 'kind': 'CXXMethod', 'type': 'auto (FString &&) -> decltype(this->Append(Forward<FString>(Str)))', 'location': {'column': 27, 'line': 438, 'offset': 19688, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'append_counted', 'arity': 1},
        'c:@S@FString@F@FString#&&$@S@FString#': {'id': 'STR05', 'kind': 'CXXConstructor', 'type': 'void (FString &&) noexcept(false)', 'location': {'column': 16, 'line': 85, 'offset': 3905, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'move', 'arity': 1},
        'c:@S@FString@F@FString#*1q#': {'id': 'STR06', 'kind': 'CXXConstructor', 'type': 'void (const WIDECHAR *)', 'location': {'column': 25, 'line': 114, 'offset': 5490, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'copy_pointer', 'arity': 1},
        'c:@S@FString@F@operator+=<#&1{n3q>#S0_#': {'id': 'STR07', 'kind': 'CXXMethod', 'type': 'auto (const char16_t (&)[3]) -> decltype(this->Append(Forward<const char16_t (&)[3]>(Str)))', 'location': {'column': 27, 'line': 438, 'offset': 19688, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'append_pointer', 'arity': 1},
        'c:@F@operator+#&1$@S@FString#*1q#': {'id': 'STR08', 'kind': 'FunctionDecl', 'type': 'FString (const FString &, const ElementType *)', 'location': {'column': 59, 'line': 667, 'offset': 29824, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'concat', 'arity': 2},
        'c:@S@FString@F@IsEmpty#1': {'id': 'STR09', 'kind': 'CXXMethod', 'type': 'bool () const', 'location': {'column': 41, 'line': 322, 'offset': 16053, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'empty_predicate', 'arity': 0},
        'c:@F@operator+#&&$@S@FString#*1q#': {'id': 'STR10', 'kind': 'FunctionDecl', 'type': 'FString (FString &&, const ElementType *)', 'location': {'column': 59, 'line': 668, 'offset': 29976, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'concat', 'arity': 2},
        'c:@F@operator+#*1q#&&$@S@FString#': {'id': 'STR11', 'kind': 'FunctionDecl', 'type': 'FString (const ElementType *, FString &&)', 'location': {'column': 59, 'line': 666, 'offset': 29666, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'concat', 'arity': 2},
        'c:@S@FString@F@FString<#$@S@TStringView>#q#q>#&&S0_#': {'id': 'STR12', 'kind': 'CXXConstructor', 'type': 'void (TStringView<char16_t> &&)', 'location': {'column': 45, 'line': 163, 'offset': 10285, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'copy_view', 'arity': 1},
        'c:@S@TStringView>#q@F@TStringView<#$@S@FString>#&1S0_#': {'id': 'STR13', 'kind': 'CXXConstructor', 'type': 'void (const FString &)', 'location': {'column': 33, 'line': 158, 'offset': 5295, 'path': 'Public/Containers/StringView.h'}, 'operation': 'borrow_counted_view', 'arity': 1},
        'c:@F@operator+#&&$@S@FString#&1S1_#': {'id': 'STR14', 'kind': 'FunctionDecl', 'type': 'FString (FString &&, const FString &)', 'location': {'column': 59, 'line': 662, 'offset': 29025, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'concat', 'arity': 2},
        'c:@S@FString@F@operator=#&1$@S@FString#': {'id': 'STR15', 'kind': 'CXXMethod', 'type': 'FString &(const FString &) noexcept(false)', 'location': {'column': 19, 'line': 88, 'offset': 4093, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'assign_copy', 'arity': 1},
        'c:@S@FString@F@operator=#&&$@S@FString#': {'id': 'STR16', 'kind': 'CXXMethod', 'type': 'FString &(FString &&) noexcept(false)', 'location': {'column': 19, 'line': 87, 'offset': 4035, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'assign_move', 'arity': 1},
        'c:@S@TStringView>#q@F@TStringView#*1q#': {'id': 'STR17', 'kind': 'CXXConstructor', 'type': 'void (const char16_t *)', 'location': {'column': 33, 'line': 125, 'offset': 3869, 'path': 'Public/Containers/StringView.h'}, 'operation': 'borrow_pointer_view', 'arity': 1},
        'c:@F@operator+#&&$@S@FString#S0_#': {'id': 'STR18', 'kind': 'FunctionDecl', 'type': 'FString (FString &&, FString &&)', 'location': {'column': 59, 'line': 664, 'offset': 29346, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'concat', 'arity': 2},
        'c:@S@FString@F@FString#I#*1q#': {'id': 'STR19', 'kind': 'CXXConstructor', 'type': 'void (int32, const WIDECHAR *)', 'location': {'column': 180, 'line': 121, 'offset': 6185, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'copy_counted_pointer', 'arity': 2},
        'c:@S@FString@F@FString#&1$@S@FString#': {'id': 'STR20', 'kind': 'CXXConstructor', 'type': 'void (const FString &) noexcept(false)', 'location': {'column': 16, 'line': 86, 'offset': 3966, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'copy', 'arity': 1},
        'c:@S@FString@F@operator+=<#&1{n2q>#S0_#': {'id': 'STR21', 'kind': 'CXXMethod', 'type': 'auto (const char16_t (&)[2]) -> decltype(this->Append(Forward<const char16_t (&)[2]>(Str)))', 'location': {'column': 27, 'line': 438, 'offset': 19688, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'append_pointer', 'arity': 1},
        'c:@S@FString@F@operator=#*1q#': {'id': 'STR22', 'kind': 'CXXMethod', 'type': 'FString &(const ElementType *)', 'location': {'column': 28, 'line': 217, 'offset': 12138, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'assign_pointer', 'arity': 1},
        'c:@S@FString@F@FString<#&1$@S@FUtf8String#u>#S0_#': {'id': 'STR23', 'kind': 'CXXConstructor', 'type': 'void (const FUtf8String &)', 'location': {'column': 45, 'line': 163, 'offset': 10285, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'decode_utf8', 'arity': 1},
        'c:@F@operator+#*1q#&1$@S@FString#': {'id': 'STR24', 'kind': 'FunctionDecl', 'type': 'FString (const ElementType *, const FString &)', 'location': {'column': 59, 'line': 665, 'offset': 29514, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'concat', 'arity': 2},
        'c:@S@FString@F@operator=<#&$@S@FString#q>#S0_#': {'id': 'STR25', 'kind': 'CXXMethod', 'type': 'FString &(FString &)', 'location': {'column': 26, 'line': 228, 'offset': 12490, 'path': 'Public/Containers/UnrealString.h.inl'}, 'operation': 'assign_range', 'arity': 1},
    }


    def __init__(self, inventories, source_bytes):
        expected = {self.ROOT + path: sha for path, sha in self.SOURCE_HASHES.items()}
        require(type(inventories) is list and inventories, 'lcer.string_api_identity_mismatch')
        require(type(source_bytes) is dict and set(source_bytes) == set(expected) and
                all(type(raw) is bytes and digest(raw) == expected[path] for path, raw in source_bytes.items()),
                'lcer.string_api_identity_mismatch')
        require(all(all(record.get('api_source_hashes', {}).get(path) == sha for path, sha in expected.items()) and
                    record.get('api_source_snapshot_unchanged') is True
                    for record in inventories), 'lcer.string_api_identity_mismatch')
        self.source_hashes = expected

    def select(self, reference, binding):
        rule = self.TARGETS.get(reference.get('target_usr'))
        if rule is None or reference.get('dynamic_call') or not binding['complete']:
            return None
        location = dict(rule['location'], path=self.ROOT + rule['location']['path'])
        if (reference.get('target_kind') != rule['kind'] or reference.get('target_type') != rule['type'] or
                reference.get('target_location') != location or len(binding['arguments']) != rule['arity']):
            return None
        receiver = binding['receiver']
        constructor = rule['kind'] == 'CXXConstructor'
        if rule['kind'] != 'FunctionDecl' and receiver is None:
            return None
        if constructor and binding['layout'] != 'constructor_result':
            return None
        args = [a['node'] for a in binding['arguments']]
        if any(value is None for value in args):
            return None
        operation = rule['operation']
        result_inputs = list(args)
        if receiver is not None and not constructor:
            result_inputs.append(receiver)
        effect = {'id': rule['id'], 'operation': operation, 'target_usr': reference['target_usr'],
                  'result_inputs': result_inputs, 'writes': [], 'aliases': [], 'conditions': [],
                  'obligations': ['api_source_compiler_correspondence_unresolved']}
        if rule['id'] in ('STR07', 'STR21'):
            # Instantiated definition inspected in both actual plugin TUs.
            # The ReturnStmt call is evaluated; trailing decltype is not.
            effect['nested_target_usr'] = 'c:@S@FString@F@Append<#1q>#*1q#'
        # Character origins survive these operations. These are may-flow
        # relations, not claims about byte equality or successful allocation.
        if operation == 'length':
            effect['value_rule'] = 'Data.ArrayNum ? Data.ArrayNum - 1 : 0; UTF-16 code units'
        elif operation == 'empty_predicate':
            effect['value_rule'] = 'Data.ArrayNum <= 1; no character scan'
        elif operation == 'empty':
            effect['value_rule'] = 'new Data pointer null, count and capacity zero'
        elif operation == 'borrow_buffer':
            effect['value_rule'] = 'allocated Data pointer if ArrayNum > 0; otherwise static empty literal'
            effect['aliases'].append({'source': receiver, 'kind': 'borrowed_buffer', 'condition': 'ArrayNum > 0'})
            effect['obligations'].append('borrowed_storage_lifetime_unresolved')
        elif operation in ('borrow_counted_view', 'borrow_pointer_view'):
            effect['value_rule'] = ('borrow FString GetData and Len; preserve embedded NUL' if operation == 'borrow_counted_view'
                                    else 'borrow input pointer; null gives zero, otherwise count to first NUL')
            effect['aliases'].append({'source': args[0], 'kind': 'borrowed_buffer', 'condition': 'always'})
            effect['obligations'].append('borrowed_storage_lifetime_unresolved')
        else:
            effect['obligations'].extend(['allocator_tracking_assertion_effects_unresolved',
                                          'string_storage_lifetime_unresolved'])
            if operation in ('copy', 'move', 'assign_copy', 'assign_move', 'assign_range', 'copy_view', 'append_counted'):
                effect['value_rule'] = 'counted code-unit transfer; embedded NUL preserved; no UTF validation'
            elif operation in ('copy_pointer', 'assign_pointer', 'append_pointer'):
                effect['value_rule'] = 'copy NUL prefix; no UTF validation'
                effect['obligations'].append('pointer_extent_and_overlap_unresolved')
            elif operation == 'copy_counted_pointer':
                effect['value_rule'] = 'copy arg0 units from arg1 only when arg1 and its first unit are nonzero'
                effect['conditions'].append('arg1 != null && arg1[0] != 0')
                effect['obligations'].append('pointer_extent_and_overlap_unresolved')
            elif operation == 'decode_utf8':
                effect['value_rule'] = 'decode counted UTF-8; source origins survive; no byte-bijection claim'
                effect['obligations'].append('utf8_conversion_effects_unresolved')
            elif operation == 'concat':
                effect['value_rule'] = 'FString operands counted; pointer operands stop at NUL'
            if operation.startswith(('assign_', 'append_')):
                effect['writes'].append({'storage': binding['receiver_storage'], 'inputs': result_inputs,
                                         'kind': 'receiver_content', 'condition': 'selected assignment or append branch'})
                effect['aliases'].append({'source': receiver, 'kind': 'receiver_reference', 'condition': 'always'})
                if not binding['receiver_storage']:
                    effect['obligations'].append('api_receiver_storage_unresolved')
            if operation in ('assign_copy', 'assign_move'):
                effect['conditions'].append('exact self-assignment leaves receiver unchanged')
            if operation == 'assign_pointer':
                effect['conditions'].append('exact Data pointer is a no-op; interior overlap is not that guard')
            if operation == 'assign_range':
                effect['conditions'].append('zero empties; <= receiver Len uses Memmove; larger replaces storage')
            if operation.startswith('append_'):
                effect['conditions'].append('zero source count leaves receiver unchanged; resize depends on capacity')
            if operation in ('move', 'assign_move'):
                condition = 'always' if operation == 'move' else 'not exact self-move'
                effect['aliases'].append({'source': args[0], 'kind': 'ownership_transfer', 'condition': condition})
                effect['writes'].append({'storage': binding['arguments'][0]['storage'], 'inputs': result_inputs,
                                         'kind': 'source_reset_after_move', 'condition': condition})
                if not binding['arguments'][0]['storage']:
                    effect['obligations'].append('moved_source_storage_unresolved')
            if operation == 'concat':
                identity = rule['id']
                moves = {'STR10': [(0, 'always')], 'STR11': [(1, 'pointer prefix empty')],
                         'STR14': [(0, 'left nonempty')],
                         'STR18': [(0, 'left nonempty'), (1, 'left empty')]}.get(identity, [])
                for index, condition in moves:
                    effect['aliases'].append({'source': args[index], 'kind': 'ownership_transfer', 'condition': condition})
                    effect['writes'].append({'storage': binding['arguments'][index]['storage'], 'inputs': result_inputs,
                                             'kind': 'source_reset_after_move', 'condition': condition})
                    if not binding['arguments'][index]['storage']:
                        effect['obligations'].append('moved_source_storage_unresolved')
        return effect


class CppJsonMemoryEffects:
    """Finite JSON/container effects with explicit alias and dispatch obligations."""

    ROOT = '/Users/Shared/Epic Games/UE_5.8/Engine/Source/Runtime/'
    SOURCE_HASHES = {
        'Core/Public/Containers/Array.h': 'a5c173f3048e387efee4d2d43c52ba43811c9a5c6916c7892b72a817a72e5109',
        'Core/Public/Containers/CompactSet.h.inl': '6b2a8a7c174f99afd347b0f98bc1112cd27a1763d1d82fedd0e3bb206029b144',
        'Core/Public/Containers/ContainerAllocationPolicies.h': '75383d5794aac3e62fd8f479575e1a1b89ad805708a17e300e31fc1f81518362',
        'Core/Public/Containers/Map.h': '6f413d22aa6cc0de5103f00ab480050fb6660ad76e945312f9d65a864eb260f6',
        'Core/Public/Containers/Map.h.inl': '4e11098f10e0f71d7452fbf2e3ec1b08b6ec4a46f2fb61532e8fd28b33f4e970',
        'Core/Public/Containers/Set.h': '7979a699931dd9466c2313b9996886433eafc33d90c3f122559ca65f70e30aba',
        'Core/Public/Containers/SharedString.h': 'aad6d6ce0b246b63ff786d0d61e1ca86b01be43bab099659591550ce5d0e2f00',
        'Core/Public/Containers/SparseSet.h.inl': '3ab72e65bae0a0c76a46fa675f5967616df7cfe760174a994ed3706e200d596d',
        'Core/Public/Containers/StringView.h': '366d0a7e3309de6154bcf9e82ce20c5c70065744e6bdfeb2536f8f770609585d',
        'Core/Public/Containers/UnrealString.h.inl': 'c2e41cf83e628a9657b03b4df591238f8f329f8242fb6448e02d791e6bf8ebe5',
        'Core/Public/Misc/UEOps.h': '17ccdb487a4058968ddb0789dfb8185039df5a2f088558565052c27fc055006e',
        'Core/Public/Serialization/BufferReader.h': 'ff308694fb7a1803dc944e30e22c4833089d240394a8626864b0e7f7d210bc10',
        'Core/Public/Templates/MemoryOps.h': '87f99a1512f812dea8fce8bd96e3c50fbde89ed4282fe5d016ee2a8f63297cd3',
        'Core/Public/Templates/SharedPointer.h': '50941bc8d4d3133ef6e44e4673b3009b89f1ecc0b81096c08021152ee9ad1e9d',
        'Core/Public/Templates/SharedPointerInternals.h': '856b28fe587da06ce0550c5a7ee5c6577d6bb2bc7c424f00ad0ae943f758d8a8',
        'Core/Public/Templates/Sorting.h': '0ec51c6f2c7a9157467d9e9e67e6f5648e69335dad1180973171e58dd5be835b',
        'Json/Private/Dom/JsonObject.cpp': '7323abc62f99848f29af9a0c0fbc0175fd2a95b65066d327e2f4e6ca74c01a4a',
        'Json/Private/Dom/JsonValue.cpp': 'c8566a1715566c65961cca7349a3e780521b7321c4951d9b33f1d6494ad93ad0',
        'Json/Private/Serialization/JsonSerializer.cpp': '15fb4b3a4530de28363873bd597b95f06a0da16431352b549b43024b65ddf4c6',
        'Json/Public/Dom/JsonObject.h': 'ed217eb63e9e37286d325467df7879972ac874033bb07af56a4498737791440c',
        'Json/Public/Dom/JsonValue.h': 'a450f70304c07fe9505fc43fba98815d0cdbb2339edcba7d5fae8d56de17aa3b',
        'Json/Public/Serialization/JsonReader.h': '42aaa57033a0d561788e521a8d18be0624981c44d0ef8ec9ef5d609ccc8f0a83',
        'Json/Public/Serialization/JsonSerializer.h': '356cbf1be630830519507521dafa5ae10791d3d17969b846d84f742ff9642baf',
    }
    TARGETS = {
        'c:@N@UE@N@JSON@N@Private@S@FJsonObjectSharedStringStorage@F@SetStringField#$@S@TStringView>#q#*1q#': {'id': 'json_set_scalar', 'kind': 'CXXMethod', 'type': 'void (FStringView, const TCHAR *)', 'location': {'column': 17, 'line': 154, 'offset': 5346, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 2, 'static': False, 'parameter_kinds': ['Record', 'Pointer']},
        'c:@N@UE@N@JSON@N@Private@S@FJsonObjectSharedStringStorage@F@SetStringField#$@S@TStringView>#q#&1$@S@FString#': {'id': 'json_set_scalar', 'kind': 'CXXMethod', 'type': 'void (FStringView, const FString &)', 'location': {'column': 17, 'line': 157, 'offset': 5589, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 2, 'static': False, 'parameter_kinds': ['Record', 'LValueReference']},
        'c:@N@UE@N@JSON@N@Private@S@FJsonObjectSharedStringStorage@F@SetNumberField#$@S@TStringView>#q#d#': {'id': 'json_set_scalar', 'kind': 'CXXMethod', 'type': 'void (FStringView, double)', 'location': {'column': 17, 'line': 142, 'offset': 4837, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 2, 'static': False, 'parameter_kinds': ['Record', 'Double']},
        'c:@N@UE@N@JSON@N@Private@S@FJsonObjectSharedStringStorage@F@SetStringField#$@S@TStringView>#q#&&$@S@FString#': {'id': 'json_set_scalar', 'kind': 'CXXMethod', 'type': 'void (FStringView, FString &&)', 'location': {'column': 17, 'line': 156, 'offset': 5511, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 2, 'static': False, 'parameter_kinds': ['Record', 'RValueReference']},
        'c:@N@UE@N@JSON@N@Private@S@FJsonObjectSharedStringStorage@F@SetBoolField#$@S@TStringView>#q#b#': {'id': 'json_set_scalar', 'kind': 'CXXMethod', 'type': 'void (FStringView, bool)', 'location': {'column': 17, 'line': 199, 'offset': 7814, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 2, 'static': False, 'parameter_kinds': ['Record', 'Bool']},
        'c:@N@UE@N@JSON@N@Private@S@FJsonObjectSharedStringStorage@F@SetField#$@S@TStringView>#q#&1$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#': {'id': 'json_set_field', 'kind': 'CXXMethod', 'type': 'void (FStringView, const TSharedPtr<FJsonValue> &)', 'location': {'column': 17, 'line': 131, 'offset': 4393, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 2, 'static': False, 'parameter_kinds': ['Record', 'LValueReference']},
        'c:@N@UE@N@JSON@N@Private@S@FJsonObjectSharedStringStorage@F@SetObjectField#$@S@TStringView>#q#&1$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#': {'id': 'json_set_object', 'kind': 'CXXMethod', 'type': 'void (FStringView, const TSharedPtr<FJsonObject> &)', 'location': {'column': 17, 'line': 227, 'offset': 9126, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 2, 'static': False, 'parameter_kinds': ['Record', 'LValueReference']},
        'c:@N@UE@N@JSON@N@Private@S@FJsonObjectSharedStringStorage@F@SetObjectField#$@S@TStringView>#q#&&$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#': {'id': 'json_set_object', 'kind': 'CXXMethod', 'type': 'void (FStringView, TSharedPtr<FJsonObject> &&)', 'location': {'column': 17, 'line': 226, 'offset': 9033, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 2, 'static': False, 'parameter_kinds': ['Record', 'RValueReference']},
        'c:@N@UE@N@JSON@N@Private@S@FJsonObjectSharedStringStorage@F@SetArrayField#$@S@TStringView>#q#&1$@S@TArray>#$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32#': {'id': 'json_set_array', 'kind': 'CXXMethod', 'type': 'void (FStringView, const TArray<TSharedPtr<FJsonValue>> &)', 'location': {'column': 17, 'line': 211, 'offset': 8323, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 2, 'static': False, 'parameter_kinds': ['Record', 'LValueReference']},
        'c:@S@FJsonObject@F@GetStringField#$@S@TStringView>#q#1': {'id': 'json_get_scalar', 'kind': 'CXXMethod', 'type': 'FString (FStringView) const', 'location': {'column': 19, 'line': 444, 'offset': 18563, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Record']},
        'c:@S@FJsonObject@F@GetNumberField#$@S@TStringView>#q#1': {'id': 'json_get_scalar', 'kind': 'CXXMethod', 'type': 'double (FStringView) const', 'location': {'column': 18, 'line': 406, 'offset': 16131, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Record']},
        'c:@S@FJsonObject@F@TryGetStringField#$@S@TStringView>#q#&$@S@FString#1': {'id': 'json_try_string', 'kind': 'CXXMethod', 'type': 'bool (FStringView, FString &) const', 'location': {'column': 16, 'line': 450, 'offset': 18861, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 2, 'static': False, 'parameter_kinds': ['Record', 'LValueReference']},
        'c:@S@FJsonObject@F@GetObjectField#$@S@TStringView>#q#1': {'id': 'json_get_object', 'kind': 'CXXMethod', 'type': 'const TSharedPtr<FJsonObject> &(FStringView) const', 'location': {'column': 42, 'line': 504, 'offset': 20793, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Record']},
        'c:@S@FJsonObject@F@GetArrayField#$@S@TStringView>#q#1': {'id': 'json_get_array', 'kind': 'CXXMethod', 'type': 'const TArray<TSharedPtr<FJsonValue>> &(FStringView) const', 'location': {'column': 49, 'line': 491, 'offset': 20256, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Record']},
        'c:@S@FJsonObject@F@TryGetField#$@S@TStringView>#q#1': {'id': 'json_try_field', 'kind': 'CXXMethod', 'type': 'TSharedPtr<FJsonValue> (FStringView) const', 'location': {'column': 34, 'line': 354, 'offset': 14533, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Record']},
        'c:@S@FJsonObject@F@HasField#$@S@TStringView>#q#1': {'id': 'json_presence', 'kind': 'CXXMethod', 'type': 'bool (FStringView) const', 'location': {'column': 16, 'line': 362, 'offset': 14786, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Record']},
        'c:@S@FJsonObject@F@HasTypedField<#V$@E@EJson1>#$@S@TStringView>#q#1': {'id': 'json_presence', 'kind': 'CXXMethod', 'type': 'bool (FStringView) const', 'location': {'column': 7, 'line': 372, 'offset': 15115, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Record']},
        'c:@S@FJsonObject@F@HasTypedField<#V$@E@EJson2>#$@S@TStringView>#q#1': {'id': 'json_presence', 'kind': 'CXXMethod', 'type': 'bool (FStringView) const', 'location': {'column': 7, 'line': 372, 'offset': 15115, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Record']},
        'c:@S@FJsonObject@F@HasTypedField<#V$@E@EJson6>#$@S@TStringView>#q#1': {'id': 'json_presence', 'kind': 'CXXMethod', 'type': 'bool (FStringView) const', 'location': {'column': 7, 'line': 372, 'offset': 15115, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Record']},
        'c:@S@FJsonObject@F@HasTypedField<#V$@E@EJson3>#$@S@TStringView>#q#1': {'id': 'json_presence', 'kind': 'CXXMethod', 'type': 'bool (FStringView) const', 'location': {'column': 7, 'line': 372, 'offset': 15115, 'path': 'Json/Public/Dom/JsonObject.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Record']},
        'c:@S@FJsonValue@F@AsString#1': {'id': 'json_value_scalar', 'kind': 'CXXMethod', 'type': 'FString () const', 'location': {'column': 19, 'line': 29, 'offset': 817, 'path': 'Json/Public/Dom/JsonValue.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@FJsonValue@F@AsBool#1': {'id': 'json_value_scalar', 'kind': 'CXXMethod', 'type': 'bool () const', 'location': {'column': 16, 'line': 35, 'offset': 1098, 'path': 'Json/Public/Dom/JsonValue.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@FJsonValue@F@AsNumber#1': {'id': 'json_value_scalar', 'kind': 'CXXMethod', 'type': 'double () const', 'location': {'column': 18, 'line': 26, 'offset': 677, 'path': 'Json/Public/Dom/JsonValue.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@FJsonValue@F@AsObject#1': {'id': 'json_value_composite', 'kind': 'CXXMethod', 'type': 'const TSharedPtr<FJsonObject> &() const', 'location': {'column': 50, 'line': 41, 'offset': 1431, 'path': 'Json/Public/Dom/JsonValue.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@FJsonValue@F@AsArray#1': {'id': 'json_value_composite', 'kind': 'CXXMethod', 'type': 'const TArray<TSharedPtr<FJsonValue>> &() const', 'location': {'column': 49, 'line': 38, 'offset': 1275, 'path': 'Json/Public/Dom/JsonValue.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1@F@TSharedPtr#*$@N@SharedPointerInternals@S@FNullTag#': {'id': 'shared_null', 'kind': 'CXXConstructor', 'type': 'void (SharedPointerInternals::FNullTag *)', 'location': {'column': 13, 'line': 706, 'offset': 30527, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Pointer']},
        'c:@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1@F@TSharedPtr<#S0_>#&1$@S@TSharedRef>#S0_#VS1_1#': {'id': 'shared_copy', 'kind': 'CXXConstructor', 'type': 'void (const TSharedRef<FJsonObject, Mode> &)', 'location': {'column': 20, 'line': 851, 'offset': 36681, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1@F@TSharedPtr<#$@S@TJsonValueString>#q>#&1$@S@TSharedRef>#S2_#VS1_1#': {'id': 'shared_copy', 'kind': 'CXXConstructor', 'type': 'void (const TSharedRef<TJsonValueString<char16_t>, Mode> &)', 'location': {'column': 20, 'line': 851, 'offset': 36681, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1@F@TSharedPtr<#$@S@FJsonValueNull>#&1$@S@TSharedRef>#S2_#VS1_1#': {'id': 'shared_copy', 'kind': 'CXXConstructor', 'type': 'void (const TSharedRef<FJsonValueNull, Mode> &)', 'location': {'column': 20, 'line': 851, 'offset': 36681, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1@F@TSharedPtr<#$@S@FJsonValueObject>#&1$@S@TSharedRef>#S2_#VS1_1#': {'id': 'shared_copy', 'kind': 'CXXConstructor', 'type': 'void (const TSharedRef<FJsonValueObject, Mode> &)', 'location': {'column': 20, 'line': 851, 'offset': 36681, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1@F@TSharedPtr#&1$@S@TSharedPtr>#S0_#VS1_1#': {'id': 'shared_copy', 'kind': 'CXXConstructor', 'type': 'void (const TSharedPtr<FJsonObject> &)', 'location': {'column': 20, 'line': 827, 'offset': 35827, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1@F@TSharedPtr<#$@S@FJsonValueNumber>#&1$@S@TSharedRef>#S2_#VS1_1#': {'id': 'shared_copy', 'kind': 'CXXConstructor', 'type': 'void (const TSharedRef<FJsonValueNumber, Mode> &)', 'location': {'column': 20, 'line': 851, 'offset': 36681, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1@F@TSharedPtr#&1$@S@TSharedPtr>#S0_#VS1_1#': {'id': 'shared_copy', 'kind': 'CXXConstructor', 'type': 'void (const TSharedPtr<FJsonValue> &)', 'location': {'column': 20, 'line': 827, 'offset': 35827, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1@F@TSharedPtr<#$@S@FJsonValueArray>#&1$@S@TSharedRef>#S2_#VS1_1#': {'id': 'shared_copy', 'kind': 'CXXConstructor', 'type': 'void (const TSharedRef<FJsonValueArray, Mode> &)', 'location': {'column': 20, 'line': 851, 'offset': 36681, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1@F@operator=#&1$@S@TSharedPtr>#S0_#VS1_1#': {'id': 'shared_copy', 'kind': 'CXXMethod', 'type': 'TSharedPtr<FJsonObject> &(const TSharedPtr<FJsonObject> &)', 'location': {'column': 32, 'line': 966, 'offset': 41788, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1@F@operator=#&&$@S@TSharedPtr>#S0_#VS1_1#': {'id': 'shared_move', 'kind': 'CXXMethod', 'type': 'TSharedPtr<FJsonObject> &(TSharedPtr<FJsonObject> &&)', 'location': {'column': 32, 'line': 975, 'offset': 42042, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['RValueReference']},
        'c:@S@TSharedRef>#$@S@FJsonObject#V$@E@ESPMode1@F@operator->#1': {'id': 'shared_deref', 'kind': 'CXXMethod', 'type': 'FJsonObject *() const', 'location': {'column': 39, 'line': 503, 'offset': 22765, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1@F@operator->#1': {'id': 'shared_deref', 'kind': 'CXXMethod', 'type': 'FJsonObject *() const', 'location': {'column': 46, 'line': 1131, 'offset': 47519, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TSharedRef>#$@S@IPlugin#V$@E@ESPMode1@F@operator->#1': {'id': 'shared_deref', 'kind': 'CXXMethod', 'type': 'IPlugin *() const', 'location': {'column': 39, 'line': 503, 'offset': 22765, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1@F@operator->#1': {'id': 'shared_deref', 'kind': 'CXXMethod', 'type': 'FJsonValue *() const', 'location': {'column': 46, 'line': 1131, 'offset': 47519, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1@F@IsValid#1': {'id': 'shared_valid', 'kind': 'CXXMethod', 'type': 'const bool () const', 'location': {'column': 38, 'line': 1109, 'offset': 46922, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1@F@operator bool#1': {'id': 'shared_valid', 'kind': 'CXXConversion', 'type': 'bool () const', 'location': {'column': 36, 'line': 1099, 'offset': 46666, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1@F@IsValid#1': {'id': 'shared_valid', 'kind': 'CXXMethod', 'type': 'const bool () const', 'location': {'column': 38, 'line': 1109, 'offset': 46922, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1@F@Reset#': {'id': 'shared_reset', 'kind': 'CXXMethod', 'type': 'void ()', 'location': {'column': 18, 'line': 1141, 'offset': 47765, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@F@MakeShared<#$@S@FJsonObject#V$@E@ESPMode1#p0>#': {'id': 'make_shared_builtin', 'kind': 'FunctionDecl', 'type': "TSharedRef<FJsonObject, (ESPMode)'\\x01'> ()", 'location': {'column': 55, 'line': 2111, 'offset': 85672, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 0, 'static': False, 'builtin_class': 'FJsonObject', 'parameter_kinds': []},
        'c:@F@MakeShared<#$@S@TJsonValueString>#q#V$@E@ESPMode1#p1&$@S@FString>#S2_#': {'id': 'make_shared_builtin', 'kind': 'FunctionDecl', 'type': "TSharedRef<TJsonValueString<char16_t>, (ESPMode)'\\x01'> (FString &)", 'location': {'column': 55, 'line': 2111, 'offset': 85672, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'builtin_class': 'TJsonValueString', 'parameter_kinds': ['LValueReference']},
        'c:@F@MakeShared<#$@S@FJsonValueNull#V$@E@ESPMode1#p0>#': {'id': 'make_shared_builtin', 'kind': 'FunctionDecl', 'type': "TSharedRef<FJsonValueNull, (ESPMode)'\\x01'> ()", 'location': {'column': 55, 'line': 2111, 'offset': 85672, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 0, 'static': False, 'builtin_class': 'FJsonValueNull', 'parameter_kinds': []},
        'c:@F@MakeShared<#$@S@FJsonValueObject#V$@E@ESPMode1#p1&1$@S@TSharedRef>#$@S@FJsonObject#VS1_1>#S2_#': {'id': 'make_shared_builtin', 'kind': 'FunctionDecl', 'type': "TSharedRef<FJsonValueObject, (ESPMode)'\\x01'> (const TSharedRef<FJsonObject> &)", 'location': {'column': 55, 'line': 2111, 'offset': 85672, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'builtin_class': 'FJsonValueObject', 'parameter_kinds': ['LValueReference']},
        'c:@F@MakeShared<#$@S@FJsonValueObject#V$@E@ESPMode1#p1&1$@S@TSharedPtr>#$@S@FJsonObject#VS1_1>#S2_#': {'id': 'make_shared_builtin', 'kind': 'FunctionDecl', 'type': "TSharedRef<FJsonValueObject, (ESPMode)'\\x01'> (const TSharedPtr<FJsonObject> &)", 'location': {'column': 55, 'line': 2111, 'offset': 85672, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'builtin_class': 'FJsonValueObject', 'parameter_kinds': ['LValueReference']},
        'c:@F@MakeShared<#$@S@TJsonValueString>#q#V$@E@ESPMode1#p1&1$@S@FString>#S2_#': {'id': 'make_shared_builtin', 'kind': 'FunctionDecl', 'type': "TSharedRef<TJsonValueString<char16_t>, (ESPMode)'\\x01'> (const FString &)", 'location': {'column': 55, 'line': 2111, 'offset': 85672, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'builtin_class': 'TJsonValueString', 'parameter_kinds': ['LValueReference']},
        'c:@F@MakeShared<#$@S@FJsonValueNumber#V$@E@ESPMode1#p1&I>#S2_#': {'id': 'make_shared_builtin', 'kind': 'FunctionDecl', 'type': "TSharedRef<FJsonValueNumber, (ESPMode)'\\x01'> (int &)", 'location': {'column': 55, 'line': 2111, 'offset': 85672, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'builtin_class': 'FJsonValueNumber', 'parameter_kinds': ['LValueReference']},
        'c:@F@MakeShared<#$@S@FJsonValueNumber#V$@E@ESPMode1#p1I>#&&I#': {'id': 'make_shared_builtin', 'kind': 'FunctionDecl', 'type': "TSharedRef<FJsonValueNumber, (ESPMode)'\\x01'> (int &&)", 'location': {'column': 55, 'line': 2111, 'offset': 85672, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'builtin_class': 'FJsonValueNumber', 'parameter_kinds': ['RValueReference']},
        'c:@F@MakeShared<#$@S@FJsonValueArray#V$@E@ESPMode1#p1&1$@S@TArray>#$@S@TSharedPtr>#$@S@FJsonValue#VS1_1#$@S@TSizedDefaultAllocator>#VI32>#S2_#': {'id': 'make_shared_builtin', 'kind': 'FunctionDecl', 'type': "TSharedRef<FJsonValueArray, (ESPMode)'\\x01'> (const TArray<TSharedPtr<FJsonValue>> &)", 'location': {'column': 55, 'line': 2111, 'offset': 85672, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'builtin_class': 'FJsonValueArray', 'parameter_kinds': ['LValueReference']},
        'c:@F@MakeShared<#$@S@FJsonValueArray#V$@E@ESPMode1#p1&$@S@TArray>#$@S@TSharedPtr>#$@S@FJsonValue#VS1_1#$@S@TSizedDefaultAllocator>#VI32>#S2_#': {'id': 'make_shared_builtin', 'kind': 'FunctionDecl', 'type': "TSharedRef<FJsonValueArray, (ESPMode)'\\x01'> (TArray<TSharedPtr<FJsonValue>> &)", 'location': {'column': 55, 'line': 2111, 'offset': 85672, 'path': 'Core/Public/Templates/SharedPointer.h'}, 'arity': 1, 'static': False, 'builtin_class': 'FJsonValueArray', 'parameter_kinds': ['LValueReference']},
        'c:@S@TArray>#C#$@S@TSizedDefaultAllocator>#VI32@F@TArray#': {'id': 'array_empty', 'kind': 'CXXConstructor', 'type': 'void ()', 'location': {'column': 46, 'line': 800, 'offset': 25270, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@TArray#': {'id': 'array_empty', 'kind': 'CXXConstructor', 'type': 'void ()', 'location': {'column': 46, 'line': 800, 'offset': 25270, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#$@S@FString#$@S@TSizedDefaultAllocator>#VI32@F@TArray#': {'id': 'array_empty', 'kind': 'CXXConstructor', 'type': 'void ()', 'location': {'column': 46, 'line': 800, 'offset': 25270, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#*1$@S@FWorldContext#$@S@TSizedDefaultAllocator>#VI32@F@TArray#': {'id': 'array_empty', 'kind': 'CXXConstructor', 'type': 'void ()', 'location': {'column': 46, 'line': 800, 'offset': 25270, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#*$@S@UWorld#$@S@TSizedDefaultAllocator>#VI32@F@TArray#': {'id': 'array_empty', 'kind': 'CXXConstructor', 'type': 'void ()', 'location': {'column': 46, 'line': 800, 'offset': 25270, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#*$@S@ULevel#$@S@TSizedDefaultAllocator>#VI32@F@TArray#': {'id': 'array_empty', 'kind': 'CXXConstructor', 'type': 'void ()', 'location': {'column': 46, 'line': 800, 'offset': 25270, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#$@S@TArray>#$@S@TObjectPtr>#$@S@AActor#$@S@TSizedDefaultAllocator>#VI32#S3_@F@TArray#': {'id': 'array_empty', 'kind': 'CXXConstructor', 'type': 'void ()', 'location': {'column': 46, 'line': 800, 'offset': 25270, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@TArray#': {'id': 'array_empty', 'kind': 'CXXConstructor', 'type': 'void ()', 'location': {'column': 46, 'line': 800, 'offset': 25270, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#*$@S@ULevel#$@S@TSizedDefaultAllocator>#VI32@F@TArray#&1$@S@TArray>#S0_#S2_#': {'id': 'array_copy', 'kind': 'CXXConstructor', 'type': 'void (const TArray<ULevel *> &)', 'location': {'column': 36, 'line': 934, 'offset': 30691, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TArray>#C#$@S@TSizedDefaultAllocator>#VI32@F@Add#&1C#': {'id': 'array_add', 'kind': 'CXXMethod', 'type': 'SizeType (const ElementType &)', 'location': {'column': 42, 'line': 2961, 'offset': 96088, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TArray>#$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@Add#&&S0_#': {'id': 'array_add', 'kind': 'CXXMethod', 'type': 'SizeType (ElementType &&)', 'location': {'column': 42, 'line': 2948, 'offset': 95718, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['RValueReference']},
        'c:@S@TArray>#$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@Add#&&S0_#': {'id': 'array_add', 'kind': 'CXXMethod', 'type': 'SizeType (ElementType &&)', 'location': {'column': 42, 'line': 2948, 'offset': 95718, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['RValueReference']},
        'c:@S@TArray>#$@S@FString#$@S@TSizedDefaultAllocator>#VI32@F@Add#&&S0_#': {'id': 'array_add', 'kind': 'CXXMethod', 'type': 'SizeType (ElementType &&)', 'location': {'column': 42, 'line': 2948, 'offset': 95718, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['RValueReference']},
        'c:@S@TArray>#*1$@S@FWorldContext#$@S@TSizedDefaultAllocator>#VI32@F@Add#&&S0_#': {'id': 'array_add', 'kind': 'CXXMethod', 'type': 'SizeType (ElementType &&)', 'location': {'column': 42, 'line': 2948, 'offset': 95718, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['RValueReference']},
        'c:@S@TArray>#*$@S@UWorld#$@S@TSizedDefaultAllocator>#VI32@F@Add#&&S0_#': {'id': 'array_add', 'kind': 'CXXMethod', 'type': 'SizeType (ElementType &&)', 'location': {'column': 42, 'line': 2948, 'offset': 95718, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['RValueReference']},
        'c:@S@TArray>#*$@S@ULevel#$@S@TSizedDefaultAllocator>#VI32@F@Add#&1S0_#': {'id': 'array_add', 'kind': 'CXXMethod', 'type': 'SizeType (const ElementType &)', 'location': {'column': 42, 'line': 2961, 'offset': 96088, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TArray>#$@S@TArray>#$@S@TObjectPtr>#$@S@AActor#$@S@TSizedDefaultAllocator>#VI32#S3_@F@Add#&1S0_#': {'id': 'array_add', 'kind': 'CXXMethod', 'type': 'SizeType (const ElementType &)', 'location': {'column': 42, 'line': 2961, 'offset': 96088, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TArray>#$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@Add#&1S0_#': {'id': 'array_add', 'kind': 'CXXMethod', 'type': 'SizeType (const ElementType &)', 'location': {'column': 42, 'line': 2961, 'offset': 96088, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TArray>#C#$@S@TSizedDefaultAllocator>#VI32@F@operator[]#I#': {'id': 'array_index', 'kind': 'CXXMethod', 'type': 'ElementType &(SizeType)', 'location': {'column': 60, 'line': 1415, 'offset': 46831, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Int']},
        'c:@S@TArray>#*$@S@UWorld#$@S@TSizedDefaultAllocator>#VI32@F@operator[]#I#': {'id': 'array_index', 'kind': 'CXXMethod', 'type': 'ElementType &(SizeType)', 'location': {'column': 60, 'line': 1415, 'offset': 46831, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Int']},
        'c:@S@TArray>#*1$@S@FWorldContext#$@S@TSizedDefaultAllocator>#VI32@F@operator[]#I#': {'id': 'array_index', 'kind': 'CXXMethod', 'type': 'ElementType &(SizeType)', 'location': {'column': 60, 'line': 1415, 'offset': 46831, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Int']},
        'c:@S@TArray>#*$@S@ULevel#$@S@TSizedDefaultAllocator>#VI32@F@operator[]#I#1': {'id': 'array_index', 'kind': 'CXXMethod', 'type': 'const ElementType &(SizeType) const', 'location': {'column': 46, 'line': 1428, 'offset': 47141, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Int']},
        'c:@S@TArray>#*$@S@ULevel#$@S@TSizedDefaultAllocator>#VI32@F@operator[]#I#': {'id': 'array_index', 'kind': 'CXXMethod', 'type': 'ElementType &(SizeType)', 'location': {'column': 60, 'line': 1415, 'offset': 46831, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Int']},
        'c:@S@TArray>#$@S@TArray>#$@S@TObjectPtr>#$@S@AActor#$@S@TSizedDefaultAllocator>#VI32#S3_@F@operator[]#I#': {'id': 'array_index', 'kind': 'CXXMethod', 'type': 'ElementType &(SizeType)', 'location': {'column': 60, 'line': 1415, 'offset': 46831, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Int']},
        'c:@S@TArray>#$@S@FString#$@S@TSizedDefaultAllocator>#VI32@F@operator[]#I#': {'id': 'array_index', 'kind': 'CXXMethod', 'type': 'ElementType &(SizeType)', 'location': {'column': 60, 'line': 1415, 'offset': 46831, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Int']},
        'c:@S@TArray>#$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@operator[]#I#': {'id': 'array_index', 'kind': 'CXXMethod', 'type': 'ElementType &(SizeType)', 'location': {'column': 60, 'line': 1415, 'offset': 46831, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Int']},
        'c:@S@TArray>#$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@operator[]#I#1': {'id': 'array_index', 'kind': 'CXXMethod', 'type': 'const ElementType &(SizeType) const', 'location': {'column': 46, 'line': 1428, 'offset': 47141, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Int']},
        'c:@S@TArray>#C#$@S@TSizedDefaultAllocator>#VI32@F@GetData#': {'id': 'array_data', 'kind': 'CXXMethod', 'type': 'ElementType *()', 'location': {'column': 60, 'line': 1271, 'offset': 42846, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#C#$@S@TSizedDefaultAllocator>#VI32@F@Num#1': {'id': 'container_cardinality', 'kind': 'CXXMethod', 'type': 'SizeType () const', 'location': {'column': 36, 'line': 1388, 'offset': 46166, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TMapBase>#$@S@FString#$@S@FConfigCommandStreamSection#$@S@FDefaultSetAllocator#$@S@TDefaultMapHashableKeyFuncs>#S0_#S1_#Vb0@F@IsEmpty#1': {'id': 'container_cardinality', 'kind': 'CXXMethod', 'type': 'bool () const', 'location': {'column': 21, 'line': 191, 'offset': 6467, 'path': 'Core/Public/Containers/Map.h.inl'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@IsEmpty#1': {'id': 'container_cardinality', 'kind': 'CXXMethod', 'type': 'bool () const', 'location': {'column': 32, 'line': 1377, 'offset': 45969, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#*1$@S@FWorldContext#$@S@TSizedDefaultAllocator>#VI32@F@Num#1': {'id': 'container_cardinality', 'kind': 'CXXMethod', 'type': 'SizeType () const', 'location': {'column': 36, 'line': 1388, 'offset': 46166, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#*$@S@ULevel#$@S@TSizedDefaultAllocator>#VI32@F@Num#1': {'id': 'container_cardinality', 'kind': 'CXXMethod', 'type': 'SizeType () const', 'location': {'column': 36, 'line': 1388, 'offset': 46166, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@Num#1': {'id': 'container_cardinality', 'kind': 'CXXMethod', 'type': 'SizeType () const', 'location': {'column': 36, 'line': 1388, 'offset': 46166, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@IsEmpty#1': {'id': 'container_cardinality', 'kind': 'CXXMethod', 'type': 'bool () const', 'location': {'column': 32, 'line': 1377, 'offset': 45969, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@Num#1': {'id': 'container_cardinality', 'kind': 'CXXMethod', 'type': 'SizeType () const', 'location': {'column': 36, 'line': 1388, 'offset': 46166, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TMapBase>#$@N@UE@S@TSharedString>#q#$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#$@S@FDefaultSetAllocator#$@S@TDefaultMapHashableKeyFuncs>#S0_#S1_#Vb0@F@Num#1': {'id': 'container_cardinality', 'kind': 'CXXMethod', 'type': 'int32 () const', 'location': {'column': 42, 'line': 197, 'offset': 6608, 'path': 'Core/Public/Containers/Map.h.inl'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TArray>#C#$@S@TSizedDefaultAllocator>#VI32@F@Reset#I#': {'id': 'array_reset', 'kind': 'CXXMethod', 'type': 'void (SizeType)', 'location': {'column': 7, 'line': 2469, 'offset': 80663, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['Int']},
        'c:@S@TArray>#C#$@S@TSizedDefaultAllocator>#VI32@F@SetNumUninitialized#I#$@E@EAllowShrinking#': {'id': 'array_uninitialized', 'kind': 'CXXMethod', 'type': 'void (SizeType, EAllowShrinking)', 'location': {'column': 7, 'line': 2582, 'offset': 84148, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 2, 'static': False, 'parameter_kinds': ['Int', 'Enum']},
        'c:Array.h@S@TArray>#$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@Sort<#$@aN@F@PlatformImages#&$@S@TArray>#$@S@TSharedPtr>#$@S@FJsonValue#VS2_1#S3_#&S0_#@Sa>#&1S4_#': {'id': 'array_sort', 'kind': 'CXXMethod', 'type': 'void (const (lambda at /Users/boandersson/Projects/CITY/CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Private/CityLiveEvidenceGameMode.cpp:310:17) &)', 'location': {'column': 18, 'line': 3670, 'offset': 120961, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:Array.h@S@TArray>#*$@S@ULevel#$@S@TSizedDefaultAllocator>#VI32@F@Sort<#$@aN@F@CollectWorlds#&$@S@TArray>#$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#S2_#S4_#&$@S@TArray>#$@S@TSharedPtr>#$@S@FJsonObject#VS8_1#S2_#&I#@Sa>#&1S3_#': {'id': 'array_sort', 'kind': 'CXXMethod', 'type': 'void (const (lambda at /Users/boandersson/Projects/CITY/CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Private/CityLiveEvidenceGameMode.cpp:418:21) &)', 'location': {'column': 18, 'line': 3670, 'offset': 120961, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:Array.h@S@TArray>#$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#$@S@TSizedDefaultAllocator>#VI32@F@Sort<#$@aN@F@CollectWorlds#&$@S@TArray>#$@S@TSharedPtr>#$@S@FJsonValue#VS2_1#S3_#S5_#&$@S@TArray>#S0_#S3_#&I#@Sa>#&1S4_#': {'id': 'array_sort', 'kind': 'CXXMethod', 'type': 'void (const (lambda at /Users/boandersson/Projects/CITY/CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Private/CityLiveEvidenceGameMode.cpp:483:21) &)', 'location': {'column': 18, 'line': 3670, 'offset': 120961, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TArray>#$@S@TObjectPtr>#$@S@AActor#$@S@TSizedDefaultAllocator>#VI32@F@operator==#&1$@S@TArray>#S0_#S2_#1': {'id': 'array_compare_unresolved_element', 'kind': 'CXXMethod', 'type': 'bool (const TArray<TObjectPtr<AActor>> &) const', 'location': {'column': 32, 'line': 1788, 'offset': 57233, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TCheckedPointerIterator>#$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'TSharedPtr<FJsonObject> &() const', 'location': {'column': 61, 'line': 235, 'offset': 7004, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TCheckedPointerIterator>#1$@S@FString#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'const FString &() const', 'location': {'column': 61, 'line': 235, 'offset': 7004, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TCheckedPointerIterator>#$@S@FString#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'FString &() const', 'location': {'column': 61, 'line': 235, 'offset': 7004, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TCheckedPointerIterator>#$@S@TSharedRef>#$@S@IPlugin#V$@E@ESPMode1#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'TSharedRef<IPlugin, ESPMode::ThreadSafe> &() const', 'location': {'column': 61, 'line': 235, 'offset': 7004, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TDereferencingIterator>#1$@S@FWorldContext#$@S@TCheckedPointerIterator>#1*v#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'const FWorldContext &() const', 'location': {'column': 60, 'line': 409, 'offset': 11014, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TCheckedPointerIterator>#1*$@S@ULevel#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'ULevel *const &() const', 'location': {'column': 61, 'line': 235, 'offset': 7004, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TCheckedPointerIterator>#*$@S@ULevel#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'ULevel *&() const', 'location': {'column': 61, 'line': 235, 'offset': 7004, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TCheckedPointerIterator>#$@S@TArray>#$@S@TObjectPtr>#$@S@AActor#$@S@TSizedDefaultAllocator>#VI32#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'TArray<TObjectPtr<AActor>> &() const', 'location': {'column': 61, 'line': 235, 'offset': 7004, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TCheckedPointerIterator>#$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'TSharedPtr<FJsonValue> &() const', 'location': {'column': 61, 'line': 235, 'offset': 7004, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TCheckedPointerIterator>#1$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'const TSharedPtr<FJsonValue> &() const', 'location': {'column': 61, 'line': 235, 'offset': 7004, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TCheckedPointerIterator>#1$@S@TSharedPtr>#$@S@FJsonObject#V$@E@ESPMode1#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'const TSharedPtr<FJsonObject> &() const', 'location': {'column': 61, 'line': 235, 'offset': 7004, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TCheckedPointerIterator>#1q#I#Vb0@F@operator*#1': {'id': 'array_iterator', 'kind': 'CXXMethod', 'type': 'const char16_t &() const', 'location': {'column': 61, 'line': 235, 'offset': 7004, 'path': 'Core/Public/Containers/Array.h'}, 'arity': 0, 'static': False, 'parameter_kinds': []},
        'c:@S@TMap>#$@N@UE@S@TSharedString>#q#$@S@TSharedPtr>#$@S@FJsonValue#V$@E@ESPMode1#$@S@FDefaultSetAllocator#$@S@TDefaultMapHashableKeyFuncs>#S0_#S1_#Vb0@F@operator=#&1$@S@TMap>#S0_#S1_#S4_#S5_#': {'id': 'map_values_copy', 'kind': 'CXXMethod', 'type': 'TMap<TSharedString<char16_t>, TSharedPtr<FJsonValue>> &(const TMap<TSharedString<char16_t>, TSharedPtr<FJsonValue>> &) noexcept(false)', 'location': {'column': 8, 'line': 1203, 'offset': 41014, 'path': 'Core/Public/Containers/Map.h.inl'}, 'arity': 1, 'static': False, 'parameter_kinds': ['LValueReference']},
        'c:@S@TJsonReaderFactory>#q@F@Create#&1$@S@FString#S': {'id': 'json_reader_string', 'kind': 'CXXMethod', 'type': 'TSharedRef<TJsonReader<TElementType_T<StringType>>> (const StringType &)', 'location': {'column': 61, 'line': 1088, 'offset': 24213, 'path': 'Json/Public/Serialization/JsonReader.h'}, 'arity': 1, 'static': True, 'parameter_kinds': ['LValueReference']},
        'c:@S@TJsonSerializer>#$@S@FJsonSerializerPolicy_JsonObject@F@Deserialize<#q>#&1$@S@TSharedRef>#$@S@TJsonReader>#q#V$@E@ESPMode1#&$@S@TSharedPtr>#$@S@FJsonObject#VS4_1#$@S@TJsonSerializer>#S0_@E@EFlags#S': {'id': 'json_deserialize_object', 'kind': 'CXXMethod', 'type': 'bool (const TSharedRef<TJsonReader<char16_t>> &, typename FJsonSerializerPolicy_JsonObject::FMapOfValues &, EFlags)', 'location': {'column': 14, 'line': 337, 'offset': 8591, 'path': 'Json/Public/Serialization/JsonSerializer.h'}, 'arity': 3, 'static': True, 'parameter_kinds': ['LValueReference', 'LValueReference', 'Enum']},
    }


    def __init__(self, inventories, source_bytes):
        expected = {self.ROOT + path: sha for path, sha in self.SOURCE_HASHES.items()}
        require(type(inventories) is list and inventories, 'lcer.json_api_identity_mismatch')
        require(type(source_bytes) is dict and set(source_bytes) == set(expected) and
                all(type(raw) is bytes and digest(raw) == expected[path] for path, raw in source_bytes.items()),
                'lcer.json_api_identity_mismatch')
        require(all(all(record.get('api_source_hashes', {}).get(path) == sha for path, sha in expected.items()) and
                    record.get('api_source_snapshot_unchanged') is True for record in inventories),
                'lcer.json_api_identity_mismatch')
        self.source_hashes = expected

    def select(self, reference, binding):
        rule = self.TARGETS.get(reference.get('target_usr'))
        if rule is None or reference.get('dynamic_call') or not binding['complete']:
            return None
        location = dict(rule['location'], path=self.ROOT + rule['location']['path'])
        if (reference.get('target_kind') != rule['kind'] or reference.get('target_type') != rule['type'] or
                reference.get('target_location') != location or len(binding['arguments']) != rule['arity']):
            return None
        method = rule['kind'] in ('CXXMethod', 'CXXConversion')
        if method and reference.get('target_method_properties', {}).get('static') != rule['static']:
            return None
        constructor = rule['kind'] == 'CXXConstructor'
        receiver = binding['receiver']
        if constructor and (binding['layout'] != 'constructor_result' or receiver is None):
            return None
        if method and not rule['static'] and receiver is None:
            return None
        if rule['static'] and (receiver is not None or binding['layout'] != 'static_method'):
            return None
        args = [argument['node'] for argument in binding['arguments']]
        if any(value is None for value in args):
            return None
        operation = rule['id']
        inputs = list(args)
        if receiver is not None and not constructor:
            inputs.append(receiver)
        effect = {'id': operation, 'operation': operation, 'target_usr': reference['target_usr'],
                  'result_inputs': list(inputs), 'writes': [], 'aliases': [], 'callbacks': [],
                  'conditions': [], 'separate_writes': True,
                  'obligations': ['api_source_compiler_correspondence_unresolved']}

        def unknown(reason):
            if reason not in effect['obligations']:
                effect['obligations'].append(reason)

        def alias(source, kind, condition='always', member=None, key=None):
            row = {'source': source, 'kind': kind, 'condition': condition}
            if member is not None:
                row['member'] = member
            if key is not None:
                row['key'] = key
            effect['aliases'].append(row)

        def write(object_node, storage, kind, sources, condition='always', member=None, key=None):
            row = {'object': object_node, 'storage': list(storage), 'kind': kind,
                   'inputs': list(sources), 'condition': condition}
            if member is not None:
                row['member'] = member
            if key is not None:
                row['key'] = key
            effect['writes'].append(row)
            if not storage or member is not None:
                unknown('api_heap_alias_unresolved')

        def receiver_write(kind, sources=None, condition='always', member=None, key=None):
            write(receiver, binding['receiver_storage'], kind, inputs if sources is None else sources,
                  condition, member, key)

        def argument_write(index, kind, sources=None, condition='always', member=None):
            argument = binding['arguments'][index]
            write(argument['node'], argument['storage'], kind, inputs if sources is None else sources,
                  condition, member)

        def lifetime():
            unknown('allocator_refcount_destructor_effects_unresolved')
            unknown('api_storage_lifetime_unresolved')

        if operation.startswith('json_set_'):
            effect['result_inputs'] = []  # void; mutation dependencies are separate.
            effect['lookup'] = 'Values key hash/equality are case-insensitive; StringSet pooling is separate'
            effect['conditions'].append('key selects receiver.Values entry; replacement releases prior value')
            receiver_write('json_field', member='Values', key=args[0])
            lifetime()
            if operation == 'json_set_scalar':
                effect['allocation'] = 'fresh builtin scalar wrapper; copied scalar content'
                if rule['parameter_kinds'][1] == 'RValueReference':
                    argument_write(1, 'source_reset_after_move', condition='actual FString argument moved into wrapper')
            elif operation == 'json_set_field':
                alias(args[1], 'shared_pointee_in_field', member='Values', key=args[0])
            elif operation == 'json_set_object':
                effect['allocation'] = 'fresh FJsonValueObject wrapper if argument valid; otherwise FJsonValueNull'
                alias(args[1], 'shared_object_in_wrapper', 'argument handle valid', 'Values', args[0])
                if rule['parameter_kinds'][1] == 'RValueReference':
                    argument_write(1, 'source_handle_reset_after_move', condition='valid actual argument handle moved')
                    effect['conditions'].append('conversion temporary is the moved handle; original TSharedRef is retained')
            else:
                effect['allocation'] = 'fresh FJsonValueArray; separate copied array slots'
                alias(args[1], 'shared_elements_in_copied_slots', member='Values', key=args[0])
        elif operation in ('json_get_scalar', 'json_try_string', 'json_get_object', 'json_get_array',
                           'json_try_field', 'json_presence'):
            effect['lookup'] = 'case-insensitive Values key lookup'
            if operation == 'json_presence':
                effect['value_rule'] = 'presence/validity; typed forms also compare public EJson tag'
                effect['conditions'].append('EJson tag does not establish dynamic class or exact key spelling')
            elif operation == 'json_try_field':
                alias(receiver, 'shared_pointee_from_field', 'entry present and valid', 'Values', args[0])
                effect['fallback'] = 'empty shared pointer'
                unknown('reference_controller_effects_unresolved')
                unknown('api_heap_alias_unresolved')
            else:
                unknown('json_value_dispatch_unresolved')
                unknown('api_heap_alias_unresolved')
                effect['conditions'].append('builtin conversion summaries require actual allocation/parse class provenance')
                if operation == 'json_try_string':
                    effect['result_inputs'] = [receiver, args[0]]
                    argument_write(1, 'string_output', [receiver, args[0]], 'lookup and virtual conversion succeed')
                    effect['fallback'] = 'false; builtin failure paths retain prior output'
                elif operation == 'json_get_scalar':
                    effect['value_rule'] = 'copied converted scalar; GetField uses EJson::None'
                    effect['fallback'] = 'default scalar with logging; failed lookup can allocate JsonNull'
                    lifetime()
                    unknown('json_logging_effects_unresolved')
                else:
                    member = 'object_shared_pointer_slot' if operation == 'json_get_object' else 'array_slots'
                    alias(receiver, 'borrowed_wrapper_member', 'successful builtin conversion', member, args[0])
                    effect['fallback'] = ('static shared mutable empty FJsonObject' if operation == 'json_get_object'
                                          else 'static empty array')
                    unknown('json_fallback_storage_unresolved')
                    unknown('json_logging_effects_unresolved')
                    lifetime()
        elif operation in ('json_value_scalar', 'json_value_composite'):
            unknown('json_value_dispatch_unresolved')
            unknown('json_logging_effects_unresolved')
            effect['conditions'].append('virtual TryGet conversion requires actual dynamic class provenance')
            if operation == 'json_value_scalar':
                effect['value_rule'] = 'copied converted scalar; conversion failure returns default'
            else:
                alias(receiver, 'borrowed_wrapper_member', 'successful builtin conversion')
                effect['fallback'] = 'static empty array or shared mutable empty object'
                unknown('json_fallback_storage_unresolved')
                unknown('api_heap_alias_unresolved')
                lifetime()
        elif operation == 'shared_null':
            effect['result_inputs'] = []
            effect['value_rule'] = 'new handle Object=null and empty reference controller'
        elif operation in ('shared_copy', 'shared_move'):
            alias(args[0], 'shared_pointee')
            unknown('reference_controller_effects_unresolved')
            if not constructor:
                receiver_write('handle_assignment')
                alias(receiver, 'receiver_reference')
                lifetime()
            if operation == 'shared_move':
                argument_write(0, 'source_handle_reset_after_move', condition='not exact self-move')
                effect['conditions'].append('move transfers handle ownership; pointed object contents remain')
        elif operation == 'shared_deref':
            alias(receiver, 'raw_pointer_to_shared_pointee')
            effect['conditions'].append('const handle does not const-qualify pointee; invalid access may assert')
            unknown('api_heap_alias_unresolved')
            unknown('api_assertion_effects_unresolved')
        elif operation == 'shared_valid':
            effect['value_rule'] = 'receiver.Object != nullptr; no pointee-content read'
        elif operation == 'shared_reset':
            effect['result_inputs'] = []
            receiver_write('handle_reset')
            effect['value_rule'] = 'receiver becomes null; other handles retain their pointee ownership'
            lifetime()
        elif operation == 'make_shared_builtin':
            effect['allocation'] = {'kind': 'fresh_object', 'class_name': rule['builtin_class']}
            lifetime()
            if rule['builtin_class'] == 'FJsonValueObject':
                alias(args[0], 'shared_object_in_fresh_wrapper')
            elif rule['builtin_class'] == 'FJsonValueArray':
                alias(args[0], 'shared_elements_in_copied_slots')
            elif rule['builtin_class'] == 'FJsonObject':
                effect['value_rule'] = 'fresh empty Values map and StringSet state'
            else:
                effect['value_rule'] = 'builtin scalar/null construction; source scalar copied'
        elif operation == 'array_empty':
            effect['result_inputs'] = []
            effect['value_rule'] = 'new empty array with exact selected allocator initialization'
        elif operation == 'array_copy':
            alias(args[0], 'raw_pointees_in_separate_array_slots')
            effect['value_rule'] = 'copy length/order and ULevel pointer identities; no world clone'
            lifetime()
        elif operation == 'array_add':
            effect['result_inputs'] = [receiver]
            effect['value_rule'] = 'return prior ArrayNum; append selected element copy or move'
            receiver_write('array_append', member='elements')
            alias(args[0], 'element_transfer_into_array')
            effect['element_type'] = reference['target_parameters'][0]['type']
            if rule['parameter_kinds'][0] == 'RValueReference':
                unknown('array_element_move_effects_unresolved')
                effect['conditions'].append('rvalue scalar/raw pointer does not reset; smart handle/string moves can reset actual argument')
            lifetime()
        elif operation in ('array_index', 'array_data', 'array_iterator'):
            alias(receiver, 'borrowed_array_element' if operation != 'array_data' else 'borrowed_array_buffer',
                  key=args[0] if operation == 'array_index' else None)
            effect['conditions'].append('index/iteration order selects element; exact element type retains pointee alias')
            unknown('api_heap_alias_unresolved')
            unknown('api_storage_lifetime_unresolved')
            unknown('api_assertion_effects_unresolved')
        elif operation == 'container_cardinality':
            effect['value_rule'] = 'container count or empty predicate; structural origins retained'
        elif operation in ('array_reset', 'array_uninitialized'):
            effect['result_inputs'] = []
            receiver_write('array_resize', member='elements')
            lifetime()
            if operation == 'array_uninitialized':
                effect['value_rule'] = 'newly exposed byte slots are uninitialized; requested count is not written content'
                unknown('uninitialized_storage_range_unresolved')
            else:
                effect['value_rule'] = 'char count becomes zero; capacity can remain or grow'
        elif operation == 'array_sort':
            effect['result_inputs'] = []
            receiver_write('array_reorder', member='elements')
            effect['callbacks'].append({'argument': args[0], 'inputs': [receiver], 'kind': 'element_comparator'})
            effect['conditions'].append('follow actual comparator body; raw pointers auto-dereference, smart pointers do not')
            unknown('api_callback_effects_unresolved')
            unknown('api_storage_lifetime_unresolved')
        elif operation == 'array_compare_unresolved_element':
            effect['value_rule'] = 'length equality and CompareItems result'
            effect['callbacks'].append({'kind': 'element_equality', 'inputs': inputs})
            unknown('array_element_comparison_effects_unresolved')
        elif operation == 'map_values_copy':
            receiver_write('map_pair_copy', member='pairs')
            alias(args[0], 'shared_keys_and_pointees_in_separate_map_slots')
            alias(receiver, 'receiver_reference')
            effect['conditions'].append('copies Values pair storage; does not copy FJsonObject.StringSet')
            lifetime()
            unknown('map_storage_configuration_effects_unresolved')
        elif operation == 'json_reader_string':
            effect['allocation'] = {'kind': 'fresh_object', 'class_name': 'TJsonStringReader<TCHAR>'}
            effect['value_rule'] = 'copy FString content; internal FBufferReader borrows that owned buffer; no file read'
            lifetime()
        elif operation == 'json_deserialize_object':
            effect['result_inputs'] = [args[0], args[2]]
            argument_write(0, 'reader_cursor', [args[0], args[2]], member='reader_state')
            argument_write(1, 'parsed_root_handle', [args[0], args[2]], 'successful GetValueFromState')
            effect['allocation'] = 'fresh builtin JSON graph only under the exact reader/policy/flags preconditions'
            effect['conditions'].append('reader must have proven TJsonStringReader<TCHAR> origin and flags must be EFlags::None')
            effect['fallback'] = 'failed parse retains prior output until successful root assignment'
            effect['lookup'] = 'duplicate/case-colliding keys can collapse through Values'
            unknown('json_reader_origin_unresolved')
            unknown('json_parser_flags_unresolved')
            unknown('api_callback_effects_unresolved')
            lifetime()
        else:
            raise ValueError('lcer.json_api_rule_unimplemented')
        return effect


class CppInputFlowGraph:
    """Conservative value/control graph from actual compiler cursor records.

    Local calls use compiler identities, including overloads. Unknown external
    effects, pointer targets, callbacks and object-sensitive storage stay
    explicit. This component cannot grant source-audit acceptance.
    """

    FUNCTIONS = frozenset(('FunctionDecl', 'CXXMethod', 'CXXConstructor', 'CXXDestructor',
                           'FunctionTemplate', 'CXXConversion'))
    STORAGE = frozenset(('VarDecl', 'ParmDecl', 'FieldDecl'))
    EXPRESSIONS = frozenset(('BinaryOperator', 'CompoundAssignOperator', 'UnaryOperator',
                             'IntegerLiteral', 'FloatingLiteral', 'StringLiteral', 'CharacterLiteral',
                             'CXXBoolLiteralExpr', 'CXXNullPtrLiteralExpr', 'DeclRefExpr', 'MemberRefExpr', 'VariableRef'))
    MAX_SUMMARY_ITERATIONS = 256
    MAX_SUMMARY_EDGES = 500000

    def __init__(self, inventories, source_bytes, api_source_bytes=None, json_api_source_bytes=None):
        require(type(inventories) is list and inventories and type(source_bytes) is dict,
                'lcer.source_inventory_invalid')
        self.inventories, self.sources = inventories, source_bytes
        for path, raw in source_bytes.items():
            require(type(path) is str and type(raw) is bytes, 'lcer.source_inventory_invalid')
        for record in inventories:
            require(record['parse_returncode'] == 0 and not record['diagnostics'] and
                    not record['visitor_errors'] and record['source_snapshot_unchanged'] and
                    record['library_snapshot_unchanged'], 'lcer.source_inventory_invalid')
            for path, raw in source_bytes.items():
                require(record['source_hashes'].get(path) == digest(raw), 'lcer.source_inventory_invalid')
        self.nodes, self.edges, self.unknown, self.calls = [], set(), set(), []
        self.cursor, self.children, self.references, self.slots, self.definitions = {}, {}, {}, {}, {}
        self.string_effects = CppStringEffects(inventories, api_source_bytes) if api_source_bytes is not None else None
        self.json_effects = CppJsonMemoryEffects(inventories, json_api_source_bytes) if json_api_source_bytes is not None else None

    def node(self, kind, label, path='', function='', usr=''):
        number = len(self.nodes)
        self.nodes.append({'id': number, 'kind': kind, 'label': label, 'path': path,
                           'function': function, 'usr': usr})
        return number

    def edge(self, source, target, kind):
        if source is not None and target is not None:
            self.edges.add((source, target, kind))

    def slot(self, usr, label, path, function, kind='storage', compiler_usr=None):
        if usr not in self.slots:
            number = self.node(kind, label, path, function, usr if compiler_usr is None else compiler_usr)
            self.nodes[number]['storage_identity'] = usr
            self.slots[usr] = number
        return self.slots[usr]

    def expression(self, node):
        return node['kind'].endswith('Expr') or node['kind'] in self.EXPRESSIONS

    def bind_external_call(self, key, reference, lvalues):
        """Retain actual external interfaces, without guessing declaration IDs."""
        cursor = self.cursor[key]
        graph = cursor['graph_id']
        reasons, arguments = set(), []
        for argument in cursor['arguments']:
            candidates = []
            for number in argument.get('cursor_nodes', ()):
                candidate = (key[0], number)
                parent, seen = candidate, set()
                while parent in self.cursor and parent != key:
                    require(parent not in seen, 'lcer.source_inventory_invalid')
                    seen.add(parent)
                    parent = (parent[0], self.cursor[parent]['parent'])
                if parent == key and candidate != key:
                    candidates.append(candidate)
            arguments.append(candidates[0] if len(candidates) == 1 else None)
            if len(candidates) != 1:
                reasons.add('call_argument_cursor_unresolved')
        parameters = reference.get('target_parameters')
        kind = reference.get('target_kind')
        receiver, receiver_storage, layout = None, set(), 'free_function'
        if kind == 'CXXConstructor':
            # The expression creates the object. Its enclosing initializer
            # binds that result to storage; no argument is the destination.
            receiver, layout = graph, 'constructor_result'
        elif kind in ('CXXMethod', 'CXXConversion'):
            properties = reference.get('target_method_properties')
            if properties is None:
                reasons.add('call_method_properties_unavailable')
            elif properties['static']:
                layout = 'static_method'
            elif (parameters is not None and cursor['name'].startswith('operator') and
                  len(arguments) == len(parameters) + 1):
                item, layout = arguments.pop(0), 'operator_receiver_argument'
                if item is not None:
                    receiver = self.cursor[item]['graph_id']
                    receiver_storage = lvalues(item)
            else:
                layout = 'member_receiver'
                members = [child for child in self.children.get(key, ())
                           if self.cursor[child]['kind'] == 'MemberRefExpr' and
                           self.references.get(child, {}).get('target_usr') == reference.get('target_usr')]
                if len(members) == 1:
                    receiver = self.cursor[members[0]]['graph_id']
                    receiver_storage = set().union(*(lvalues(child) for child in self.children.get(members[0], ())))
            if properties is not None and not properties['static'] and receiver is None:
                reasons.add('call_receiver_unresolved')
        elif kind != 'FunctionDecl':
            reasons.add('call_target_kind_unresolved')
        if parameters is None or len(parameters) != len(arguments):
            reasons.add('call_parameter_binding_unresolved')
        bound = []
        for index, argument in enumerate(arguments):
            parameter = parameters[index] if parameters is not None and index < len(parameters) else None
            bound.append({'index': index, 'node': self.cursor[argument]['graph_id'] if argument is not None else None,
                          'storage': sorted(lvalues(argument)) if argument is not None else [],
                          'parameter': parameter})
        for reason in reasons:
            self.unknown.add((graph, reason))
        return {'layout': layout, 'receiver': receiver, 'receiver_storage': sorted(receiver_storage),
                'arguments': bound, 'complete': not reasons}

    def build(self):
        # Each TU retains its actual cursor tree. Shared declarations use USRs;
        # repeated header definitions do not acquire invented compiler IDs.
        for unit, record in enumerate(self.inventories):
            for ordinal, n in enumerate(record['nodes']):
                require(n['id'] == ordinal, 'lcer.source_inventory_invalid')
                key = (unit, n['id'])
                self.cursor[key] = n
                label = n['name']
                if n['start']['path'] in self.sources and n['end']['path'] == n['start']['path']:
                    label = self.sources[n['start']['path']][n['start']['offset']:n['end']['offset']].decode('utf-8')
                self.node(n['kind'], label, n['location']['path'], n['function'], n['usr'])
                n = dict(n)
                n['graph_id'] = len(self.nodes) - 1
                self.cursor[key] = n
                self.children.setdefault((unit, n['parent']), []).append(key)
            for ref in record['references']:
                self.references[(unit, ref['node'])] = ref

        def parent_function(key):
            seen = set()
            while key in self.cursor:
                require(key not in seen, 'lcer.source_inventory_invalid')
                seen.add(key)
                n = self.cursor[key]
                if n['kind'] in self.FUNCTIONS:
                    return key
                key = (key[0], n['parent'])
            return None

        owners = {key: parent_function(key) for key in self.cursor}
        for key, n in self.cursor.items():
            if n['kind'] == 'LambdaExpr':
                method = self.cursor.get((key[0], n.get('lambda_operator_node')))
                if (method is None or method['parent'] != key[1] or method['kind'] != 'CXXMethod' or
                        not method['usr'] or n.get('lambda_closure', {}).get('operator_usrs') != [method['usr']]):
                    self.unknown.add((n['graph_id'], 'anonymous_callable_identity_unresolved'))
                continue
            if n['kind'] not in self.FUNCTIONS or (not n['definition'] and n['kind'] != 'LambdaExpr'):
                continue
            if not n['usr']:
                self.unknown.add((n['graph_id'], 'anonymous_callable_identity_unresolved'))
                continue
            entry = self.definitions.get(n['usr'])
            if entry is None:
                entry = {'usr': n['usr'], 'name': n['qualified'], 'key': key,
                         'activation': self.node('activation', n['qualified'], n['location']['path'], n['qualified'], n['usr']),
                         'return': self.node('return_slot', n['qualified'], n['location']['path'], n['qualified'], n['usr']),
                         'parameters': [], 'receiver': None}
                if n['kind'] in ('CXXMethod', 'CXXConstructor', 'CXXDestructor', 'CXXConversion') and not n.get('method_properties', {}).get('static', False):
                    entry['receiver'] = self.node('receiver_slot', 'this', n['location']['path'], n['qualified'], n['usr'])
                self.definitions[n['usr']] = entry
            for ordinal, child in enumerate(k for k in self.children.get(key, ()) if self.cursor[k]['kind'] == 'ParmDecl'):
                parameter = self.cursor[child]
                identity = parameter['usr'] or 'parameter-slot:' + n['usr'] + ':%d' % ordinal
                slot = self.slot(identity, parameter['name'], parameter['location']['path'], n['qualified'],
                                 compiler_usr=parameter['usr'])
                if ordinal >= len(entry['parameters']):
                    entry['parameters'].append({'slot': slot, 'type': parameter['type'],
                                                'type_kind': parameter.get('type_kind'), 'key': child})

        storage = {}
        for key, n in self.cursor.items():
            if n['kind'] not in self.STORAGE:
                continue
            owner = self.cursor.get(owners[key], {})
            identity = n['usr']
            if not identity and n['kind'] == 'ParmDecl' and owner.get('usr'):
                parameters = [k for k in self.children.get(owners[key], ()) if self.cursor[k]['kind'] == 'ParmDecl']
                if key in parameters:
                    identity = 'parameter-slot:' + owner['usr'] + ':%d' % parameters.index(key)
                    storage[key] = self.slot(identity, n['name'], n['location']['path'], n['function'], compiler_usr='')
                    continue
            if not identity:
                self.unknown.add((n['graph_id'], 'storage_identity_unresolved'))
                continue
            storage[key] = self.slot(identity, n['name'], n['location']['path'], n['function'])
            if n['kind'] == 'FieldDecl':
                self.unknown.add((n['graph_id'], 'object_sensitive_storage_unresolved'))

        defined_variables = {n['usr'] for n in self.cursor.values()
                             if n['kind'] == 'VarDecl' and n['definition'] and n['usr']}
        external_storage = {n['usr'] for n in self.cursor.values()
                            if n['kind'] == 'VarDecl' and n['usr'] and n['usr'] not in defined_variables}
        for identity in external_storage:
            self.nodes[self.slots[identity]]['kind'] = 'external_storage'
        for key, ref in self.references.items():
            if ref['kind'] not in ('DeclRefExpr', 'MemberRefExpr', 'VariableRef'):
                continue
            graph = self.cursor[key]['graph_id']
            if 'target_kind' not in ref:
                self.unknown.add((graph, 'reference_target_kind_unavailable'))
                continue
            if ref['target_kind'] not in self.STORAGE:
                continue
            identity = ref['target_usr']
            if not identity:
                self.unknown.add((graph, 'referenced_storage_identity_unresolved'))
                continue
            if identity not in self.slots:
                slot = self.slot(identity, ref['target'], ref['target_location']['path'], '', 'external_storage')
                self.nodes[slot]['declaration_kind'] = ref['target_kind']
                self.nodes[slot]['type'] = ref['target_type']
                external_storage.add(identity)
            if identity in external_storage:
                # A declaration outside the plugin does not by itself tell
                # whether this is platform state, world state or a JSON field.
                self.unknown.add((graph, 'external_storage_origin_unresolved'))

        capture_bindings = {}
        scalar_capture_kinds = frozenset(('Bool', 'Char_U', 'UChar', 'Char_S', 'SChar', 'WChar', 'Char16',
                                         'Char32', 'UShort', 'UInt', 'ULong', 'ULongLong', 'UInt128',
                                         'Short', 'Int', 'Long', 'LongLong', 'Int128', 'Float', 'Double',
                                         'LongDouble', 'Half', 'Float128', 'Enum'))
        for key, n in self.cursor.items():
            if n['kind'] != 'LambdaExpr':
                continue
            closure = n.get('lambda_closure', {})
            fields = closure.get('fields', [])
            method = self.cursor.get((key[0], n.get('lambda_operator_node')), {})
            for field in fields:
                capture = field.get('capture_reference', {})
                declaration = capture.get('declaration', {})
                identity = declaration.get('usr')
                mode = ('reference' if field['type_kind'] == 'LValueReference' else
                        'copy' if field['type_kind'] in scalar_capture_kinds else None)
                if (not mode or not identity or identity not in self.slots or
                        capture.get('binding_basis') != 'unique_explicit_capture_location' or
                        capture.get('declaration_location') == field['location'] or
                        not method.get('usr') or closure.get('operator_usrs') != [method['usr']]):
                    self.unknown.add((n['graph_id'], 'lambda_capture_semantics_unresolved'))
                    continue
                # Capture fields have no public USR. Keep that fact. The
                # separate storage key binds the compiler closure/layout and
                # source bytes; it is not an invented declaration identity.
                layout = {'source_sha256': digest(self.sources[n['location']['path']]),
                          'closure_usr': closure['usr'], 'ordinal': field['ordinal'],
                          'location': field['location'], 'type': field['type'],
                          'offset_bits': field['offset_bits']}
                storage_id = 'lambda-capture:' + digest(json.dumps(layout, sort_keys=True).encode('utf-8'))
                slot = self.slot(storage_id, declaration['name'], n['location']['path'], method['qualified'],
                                 'capture_storage', compiler_usr=field['usr'])
                self.nodes[slot].update(capture_layout=layout, capture_mode=mode, captured_usr=identity)
                capture_bindings[(key[0], method['usr'], identity)] = slot
                self.edge(self.slots[identity], slot, 'capture_' + mode)
                if mode == 'reference':
                    self.edge(slot, self.slots[identity], 'capture_reference')
                # Distinct closure objects at repeated executions still need
                # object-sensitive lifetime/receiver analysis.
                self.unknown.add((n['graph_id'], 'lambda_instance_storage_unresolved'))

        def referenced_slot(key, ref):
            owner = self.cursor.get(owners[key], {})
            return capture_bindings.get((key[0], owner.get('usr'), ref['target_usr']),
                                        self.slots.get(ref['target_usr']))

        def lvalues(key):
            n = self.cursor[key]
            ref = self.references.get(key)
            if n['kind'] == 'CXXThisExpr':
                owner = self.cursor.get(owners[key], {})
                receiver = self.definitions.get(owner.get('usr'), {}).get('receiver')
                return {receiver} if receiver is not None else set()
            if ref and ref['target_usr'] in self.slots:
                return {referenced_slot(key, ref)}
            if n['kind'] in ('UnexposedExpr', 'ParenExpr'):
                return set().union(*(lvalues(k) for k in self.children.get(key, ())))
            if n['kind'] in ('ArraySubscriptExpr', 'UnaryOperator'):
                self.unknown.add((n['graph_id'], 'indirect_storage_target_unresolved'))
            return set()

        # Expressions and memory retain origins. A value edge does not prove
        # alias identity, successful execution, or dominance.
        for key, n in self.cursor.items():
            graph = n['graph_id']
            children = self.children.get(key, ())
            owner = self.cursor.get(owners[key], {})
            function = self.definitions.get(owner.get('usr'))
            if function and key != owners[key]:
                self.edge(function['activation'], graph, 'activation')
            ref = self.references.get(key)
            if n['kind'] in ('DeclRefExpr', 'MemberRefExpr', 'VariableRef') and ref:
                if ref['target_usr'] in self.slots:
                    self.edge(referenced_slot(key, ref), graph, 'storage_read')
            if n['kind'] == 'CXXThisExpr' and function:
                self.edge(function['receiver'], graph, 'receiver_read')
            # A known helper's result is derived from its body below. Merely
            # evaluating an unused argument does not make it the result.
            local_call = (n['kind'] == 'CallExpr' and ref and
                          ref.get('target_usr') in self.definitions and not ref.get('dynamic_call'))
            if self.expression(n) and not local_call:
                for child in children:
                    if self.expression(self.cursor[child]):
                        self.edge(self.cursor[child]['graph_id'], graph, 'expression_value')
            if key in storage:
                initializers = [child for child in children if self.expression(self.cursor[child])]
                for child in initializers:
                    self.edge(self.cursor[child]['graph_id'], storage[key], 'initialization')
                if initializers and n.get('type_kind') in ('LValueReference', 'RValueReference'):
                    targets = lvalues(initializers[0]) if len(initializers) == 1 else set()
                    if targets:
                        for target in targets:
                            self.edge(target, storage[key], 'reference_alias')
                            self.edge(storage[key], target, 'reference_alias')
                    else:
                        self.unknown.add((graph, 'reference_initialization_unresolved'))
                elif initializers and n.get('type_kind') == 'Pointer':
                    self.unknown.add((graph, 'pointer_initialization_unresolved'))
                elif initializers and n.get('type_kind') is None:
                    self.unknown.add((graph, 'storage_type_kind_unavailable'))
            if n['kind'] == 'ReturnStmt' and function:
                for child in children:
                    if self.expression(self.cursor[child]):
                        self.edge(self.cursor[child]['graph_id'], function['return'], 'return_value')
                self.edge(function['activation'], function['return'], 'return_activation')
            if n['binary_operator'] == '=' and len(children) == 2:
                for target in lvalues(children[0]):
                    self.edge(self.cursor[children[1]]['graph_id'], target, 'assignment')
                    if self.nodes[target]['kind'] == 'external_storage':
                        self.unknown.add((graph, 'external_storage_write_unresolved'))
            elif n['kind'] == 'CompoundAssignOperator' or n['unary_operator'] in ('++', '--'):
                if children:
                    for target in lvalues(children[0]):
                        self.edge(graph, target, 'compound_assignment')
            if n['kind'] in ('IfStmt', 'WhileStmt', 'ForStmt', 'DoStmt', 'SwitchStmt', 'ConditionalOperator'):
                expressions = [k for k in children if self.expression(self.cursor[k])]
                for condition in expressions:
                    pending = list(children)
                    while pending:
                        child = pending.pop()
                        if child == condition:
                            continue
                        self.edge(self.cursor[condition]['graph_id'], self.cursor[child]['graph_id'], 'may_control')
                        pending.extend(self.children.get(child, ()))
                self.unknown.add((graph, 'control_flow_dominance_unresolved'))
            if n['binary_operator'] in ('&&', '||') and len(children) == 2:
                pending = [children[1]]
                while pending:
                    child = pending.pop()
                    self.edge(self.cursor[children[0]]['graph_id'], self.cursor[child]['graph_id'], 'short_circuit_control')
                    pending.extend(self.children.get(child, ()))
                self.unknown.add((graph, 'control_flow_dominance_unresolved'))
            if n['kind'] in ('CXXTryStmt', 'CXXThrowExpr', 'CXXCatchStmt', 'GotoStmt', 'IndirectGotoStmt',
                             'CXXNewExpr', 'CXXDeleteExpr', 'CXXDynamicCastExpr'):
                self.unknown.add((graph, 'language_effect_unresolved'))

        node_owners = {n['graph_id']: self.cursor.get(owners[key], {}).get('usr')
                       for key, n in self.cursor.items()}
        shared = set()
        for key, slot in storage.items():
            n = self.cursor[key]
            owner = self.cursor.get(owners[key], {}).get('usr')
            if n['kind'] == 'FieldDecl' or not owner or (n['kind'] == 'VarDecl' and n.get('global_storage', True)):
                shared.add(slot)
                if n['kind'] == 'VarDecl' and owner and 'global_storage' not in n:
                    self.unknown.add((n['graph_id'], 'storage_duration_unresolved'))
            else:
                node_owners[slot] = owner
        shared.update(self.slots[identity] for identity in external_storage)
        shared.update(capture_bindings.values())
        for usr, definition in self.definitions.items():
            for number in [definition['activation'], definition['return'], definition['receiver']] + [
                    p['slot'] for p in definition['parameters']]:
                if number is not None:
                    node_owners[number] = usr
        for key, ref in self.references.items():
            if ref.get('target_usr') not in self.slots:
                continue
            slot = referenced_slot(key, ref)
            graph = self.cursor[key]['graph_id']
            if (slot not in shared and node_owners.get(slot) and
                    node_owners.get(graph) != node_owners[slot]):
                # Unsupported captures can still refer to an enclosing local.
                # Keep that possible shared path and its unresolved lifetime;
                # call separation must not silently erase the captured input.
                shared.add(slot)
                self.unknown.add((graph, 'cross_function_storage_unresolved'))

        transfers = []
        for key, n in self.cursor.items():
            if n['kind'] != 'CallExpr':
                continue
            graph = n['graph_id']
            ref = self.references.get(key, {})
            target = self.definitions.get(ref.get('target_usr'))
            call = {'node': graph, 'target_usr': ref.get('target_usr', ''),
                    'target': ref.get('target', ''), 'local_definition': target is not None}
            self.calls.append(call)
            if target is None or ref.get('dynamic_call'):
                binding = self.bind_external_call(key, ref, lvalues)
                call['binding'] = binding
                effect = self.string_effects.select(ref, binding) if self.string_effects else None
                if effect is None and self.json_effects:
                    effect = self.json_effects.select(ref, binding)
                if effect is not None:
                    call['api_effect'] = effect
                    # Replace the blanket expression-result assumption with
                    # the selected API's actual value and write dependencies.
                    self.edges = {edge for edge in self.edges if not (edge[1] == graph and edge[2] == 'expression_value')}
                    for source in effect['result_inputs']:
                        self.edge(source, graph, 'api_result_value')
                    for write in effect['writes']:
                        write_node = graph
                        if effect.get('separate_writes'):
                            write_node = self.node('api_write', effect['operation'] + ':' + write['kind'],
                                                   n['location']['path'], n['function'], ref.get('target_usr', ''))
                            write['node'] = write_node
                            node_owners[write_node] = node_owners.get(graph)
                            for source in write['inputs']:
                                self.edge(source, write_node, 'api_write_value')
                            for source, destination, kind in tuple(self.edges):
                                if destination == graph and kind in ('activation', 'may_control', 'short_circuit_control'):
                                    self.edge(source, write_node, 'api_write_control')
                            # Symbolic writes remain observable effects while
                            # the heap/alias layer resolves their destination.
                            self.unknown.add((write_node, 'api_memory_destination_unresolved'))
                        for destination in write['storage']:
                            self.edge(write_node, destination, 'api_' + write['kind'])
                    for reason in effect['obligations']:
                        self.unknown.add((graph, reason))
                    continue
                # A void external call can still write through its arguments.
                # Keep those paths even while its effects remain unresolved.
                for argument in binding['arguments']:
                    parameter = argument['parameter'] or {}
                    if parameter.get('type_kind') in ('LValueReference', 'RValueReference', 'Pointer'):
                        for destination in argument['storage']:
                            self.edge(graph, destination, 'external_may_reference_write')
                for destination in binding['receiver_storage']:
                    self.edge(graph, destination, 'external_may_receiver_write')
                self.unknown.add((graph, 'dynamic_call_unresolved' if ref.get('dynamic_call') else 'external_call_effect_unresolved'))
                continue
            # Template parameters never receive actual arguments. Each call
            # owns its interface; only body-derived transfers cross it.
            ports = {}
            for template in [target['activation'], target['return'], target['receiver']] + [
                    p['slot'] for p in target['parameters']]:
                if template is None:
                    continue
                original = self.nodes[template]
                port = self.node('call_' + original['kind'], original['label'], original['path'],
                                 original['function'], original['usr'])
                self.nodes[port].update(template_node=template, call_node=graph)
                ports[template] = port
                node_owners[port] = node_owners.get(graph)
            call['ports'] = [{'template': template, 'node': port} for template, port in sorted(ports.items())]
            transfers.append((call, target, ports))
            for source, destination, kind in tuple(self.edges):
                if destination == graph and kind in ('activation', 'may_control', 'short_circuit_control'):
                    self.edge(source, ports[target['activation']], 'call_control')
            self.edge(ports[target['return']], graph, 'call_return')
            arguments = []
            for argument in n['arguments']:
                candidates = []
                for number in argument.get('cursor_nodes', ()):
                    candidate = (key[0], number)
                    parent = candidate
                    while parent in self.cursor and parent != key:
                        parent = (parent[0], self.cursor[parent]['parent'])
                    if parent == key and candidate != key:
                        candidates.append(candidate)
                if len(candidates) == 1:
                    arguments.append(candidates[0])
                else:
                    arguments.append(None)
                    self.unknown.add((graph, 'call_argument_cursor_unresolved'))
            # Compiler overloaded operator arguments can contain the receiver.
            # Ordinary method calls retain it in their member expression.
            if target['receiver'] is not None:
                if len(arguments) == len(target['parameters']) + 1 and n['name'].startswith('operator'):
                    receiver = arguments.pop(0)
                    if receiver is not None:
                        self.edge(self.cursor[receiver]['graph_id'], ports[target['receiver']], 'receiver_argument')
                else:
                    members = [k for k in self.children.get(key, ()) if self.cursor[k]['kind'] == 'MemberRefExpr']
                    if len(members) == 1:
                        self.edge(self.cursor[members[0]]['graph_id'], ports[target['receiver']], 'receiver_argument')
                    else:
                        self.unknown.add((graph, 'call_receiver_unresolved'))
            if len(arguments) != len(target['parameters']):
                self.unknown.add((graph, 'call_parameter_binding_unresolved'))
            for argument, parameter in zip(arguments, target['parameters']):
                if argument is None:
                    continue
                self.edge(self.cursor[argument]['graph_id'], ports[parameter['slot']], 'call_argument')
                parameter_kind = parameter['type_kind']
                if parameter_kind in ('LValueReference', 'RValueReference', 'Pointer'):
                    # The write edge is conservative, including const handles:
                    # handle constness alone does not freeze their pointees.
                    for destination in lvalues(argument):
                        self.edge(ports[parameter['slot']], destination, 'may_reference_write')
                    self.unknown.add((graph, 'reference_call_effect_unresolved'))
                elif parameter_kind is None:
                    self.unknown.add((graph, 'parameter_type_kind_unavailable'))

        summaries = self.summarize_calls(node_owners, shared, transfers)
        return {'files': [{'path': path, 'sha256': digest(raw), 'size_bytes': len(raw)}
                          for path, raw in sorted(self.sources.items())],
                'nodes': self.nodes,
                'edges': [{'source': source, 'target': target, 'kind': kind}
                          for source, target, kind in sorted(self.edges)],
                'functions': [{'usr': usr, 'name': row['name'], 'activation': row['activation'],
                               'return': row['return'], 'parameters': [p['slot'] for p in row['parameters']]}
                              for usr, row in sorted(self.definitions.items())],
                'calls': self.calls,
                'call_summaries': summaries,
                'unclassified': [{'node': node, 'reason': reason} for node, reason in sorted(self.unknown)],
                'source_audit_complete': False}

    def summarize_calls(self, owners, shared, transfers):
        """Finite, monotone value/write summaries, instantiated per call.

        Shared storage is a boundary: a write is exported; a read starts from
        that storage. Traversal never borrows another function's body. Actual
        external call sites remain possible input origins and unresolved
        effects. Direct effect dependencies are retained separately for the
        later source-policy analysis; these summaries grant no acceptance.
        """
        external = {c['node'] for c in self.calls if 'ports' not in c}
        roots, outputs, effects = {}, {}, {}
        for usr, definition in self.definitions.items():
            parameters = {p['slot'] for p in definition['parameters']}
            roots[usr] = parameters | {definition['activation']} | shared | external
            outputs[usr] = {definition['return']} | {
                p['slot'] for p in definition['parameters']
                if p['type_kind'] in ('LValueReference', 'RValueReference', 'Pointer')}
            if definition['receiver'] is not None:
                roots[usr].add(definition['receiver'])
                outputs[usr].add(definition['receiver'])
            effects[usr] = {c['node'] for c in self.calls if owners.get(c['node']) == usr}
            effects[usr].update(node for node, _ in self.unknown if owners.get(node) == usr)

        def dependencies(usr, destination, incoming):
            pending, seen, found = [destination], set(), set()
            while pending:
                node = pending.pop()
                if node in seen:
                    continue
                seen.add(node)
                if node in roots[usr]:
                    found.add(node)
                # On entering a shared cell, use its current value. Following
                # its writers here would mix invocations and other bodies.
                if node in shared and node != destination:
                    continue
                for source in incoming.get(node, ()):
                    if owners.get(source) == usr or source in shared or source in external:
                        pending.append(source)
            return found

        summaries = {usr: set() for usr in self.definitions}
        # Recursive calls use a least fixed point over a finite relation. A
        # budget failure is explicit; a partial relation is never returned.
        for iteration in range(self.MAX_SUMMARY_ITERATIONS):
            incoming = {}
            for source, target, _ in self.edges:
                incoming.setdefault(target, set()).add(source)
                if target in shared and owners.get(source) in outputs:
                    outputs[owners[source]].add(target)
            changed = False
            for usr in self.definitions:
                for destination in outputs[usr]:
                    summaries[usr].update((source, destination) for source in dependencies(usr, destination, incoming))
            for call, target, ports in transfers:
                for source, destination in summaries[target['usr']]:
                    source, destination = ports.get(source, source), ports.get(destination, destination)
                    if source != destination and (source, destination, 'call_summary') not in self.edges:
                        self.edge(source, destination, 'call_summary')
                        changed = True
            require(len(self.edges) <= self.MAX_SUMMARY_EDGES, 'lcer.call_summary_budget_exceeded')
            if not changed:
                break
        else:
            raise ValueError('lcer.call_summary_budget_exceeded')
        result = []
        call_by_node = {call['node']: (target, ports) for call, target, ports in transfers}
        for usr in sorted(self.definitions):
            effect_rows = []
            for node in sorted(effects[usr]):
                inputs = dependencies(usr, node, incoming)
                effect = {'node': node}
                if node in call_by_node:
                    target, ports = call_by_node[node]
                    bindings = []
                    for template, port in sorted(ports.items()):
                        if template == target['return']:
                            continue
                        origins = dependencies(usr, port, incoming)
                        inputs.update(origins)
                        bindings.append({'template': template, 'node': port, 'inputs': sorted(origins)})
                    # A void helper can still publish an argument. Keep the
                    # input mapping for recursive policy inspection of its
                    # body, independently of the helper's return value.
                    effect['bindings'] = bindings
                effect['inputs'] = sorted(inputs)
                effect_rows.append(effect)
            result.append({'usr': usr, 'transfers': [{'source': a, 'target': b} for a, b in sorted(summaries[usr])],
                           'effects': effect_rows, 'fixed_point_iterations': iteration + 1})
        return result


def _cpp_local_call_index(records):
    definitions, owned, calls, references, nodes = {}, {}, [], {}, {}
    for unit, record in enumerate(records):
        for index, node in enumerate(record['nodes']):
            require(node['id'] == index, 'lcer.source_inventory_invalid')
            key = (unit, index)
            nodes[key] = node
            if node['kind'] in CppInputFlowGraph.FUNCTIONS and node['definition']:
                require(bool(node['usr']), 'lcer.source_inventory_invalid')
                previous = definitions.setdefault(node['usr'], node)
                require(previous['qualified'] == node['qualified'], 'lcer.source_inventory_invalid')
        for reference in record['references']:
            key = (unit, reference['node'])
            require(key in nodes and key not in references, 'lcer.source_inventory_invalid')
            references[key] = reference
    for key, node in nodes.items():
        cursor, seen = key, set()
        while cursor in nodes:
            require(cursor not in seen, 'lcer.source_inventory_invalid')
            seen.add(cursor)
            current = nodes[cursor]
            if current['kind'] in CppInputFlowGraph.FUNCTIONS and current['definition']:
                owned[key] = current['usr']
                break
            cursor = (cursor[0], current['parent'])
        if node['kind'] == 'CallExpr':
            reference = references.get(key, {})
            calls.append({'key': key, 'owner': owned.get(key),
                          'target': reference.get('target_usr'),
                          'dynamic': reference.get('dynamic_call')})
    return definitions, owned, calls, references, nodes


class CppCommandAuthority:
    """Enforce the explicit native command callers from compiler identities.

    This checks local invocation authority, including protected method-value
    escapes and controller-to-helper paths. Data origins, queue contents,
    callbacks and external effects remain obligations of the full audit.
    A passing component report cannot grant source-audit acceptance.
    """

    ROLES = {
        'worker': 'FLCERInputThread::Run',
        'queue': 'ACityLiveEvidenceGameMode::EnqueueInput',
        'tick': 'ACityLiveEvidenceGameMode::Tick',
        'dispatch': 'ACityLiveEvidenceGameMode::Dispatch',
        'interact': 'ACityLiveEvidenceResource::Interact',
        'controller': 'ACityLiveEvidenceGameMode::RestartPlayer',
    }
    CALLERS = {'queue': 'worker', 'dispatch': 'tick', 'interact': 'dispatch'}

    def __init__(self, inventories, source_bytes):
        # Reuse the graph's source/compiler snapshot validation, without
        # building or trusting a caller-supplied call graph.
        CppInputFlowGraph(inventories, source_bytes)
        self.records, self.sources = inventories, source_bytes

    def check(self):
        definitions, owned, calls, references, nodes = _cpp_local_call_index(self.records)
        identities = {}
        for role, name in self.ROLES.items():
            matches = [usr for usr, node in definitions.items() if node['qualified'] == name]
            require(len(matches) == 1, 'lcer.source_inventory_invalid')
            node = definitions[matches[0]]
            require(node['kind'] == 'CXXMethod' and node['location']['path'] in self.sources,
                    'lcer.source_inventory_invalid')
            identities[role] = matches[0]
        protected = {identities[role]: identities[caller] for role, caller in self.CALLERS.items()}
        call_by_key = {row['key']: row for row in calls}
        adjacency = {}
        for call in calls:
            if call['owner'] and call['target'] in definitions:
                # A virtual call's declared local body remains a possible
                # target. Uncertain dispatch must not erase a forbidden path.
                adjacency.setdefault(call['owner'], []).append(call)

        def reject(key, input_kind):
            node = nodes[key]
            function = definitions[owned[key]]['qualified'] if key in owned else '<module>'
            target = references.get(key, {}).get('target', node['name'])
            error = SourceInputForbidden(node['location']['path'], function, target,
                                         node['location']['line'], input_kind)
            error.compiler_identity = {'caller_usr': owned.get(key),
                                       'callee_usr': references.get(key, {}).get('target_usr')}
            raise error

        # A method value can be stored, returned, captured or passed through
        # an external helper. Only the member expression of the actual direct
        # call may refer to a protected endpoint. Declared bodies are not uses.
        for key, reference in references.items():
            if reference.get('target_usr') not in protected:
                continue
            current, direct = key, None
            while current in nodes:
                if current in call_by_key:
                    direct = call_by_key[current]
                    break
                if nodes[current]['kind'] in CppInputFlowGraph.FUNCTIONS:
                    break
                current = (current[0], nodes[current]['parent'])
            if (direct is None or direct['target'] != reference['target_usr'] or direct['dynamic'] or
                    direct['owner'] != protected[reference['target_usr']]):
                reject(key, 'world' if owned.get(key) == identities['controller'] else 'command')

        # A controller shortcut into a permitted caller is also forbidden.
        # Follow every resolved local helper, not just calls named Interact.
        pending = [(identities['controller'], [])]
        reached = set()
        while pending:
            owner, chain = pending.pop(0)
            if owner in reached:
                continue
            reached.add(owner)
            for call in adjacency.get(owner, ()):
                path = chain + [call['key']]
                if call['target'] in protected or call['target'] in (identities['worker'], identities['tick']):
                    try:
                        reject(path[0], 'world')
                    except SourceInputForbidden as error:
                        error.call_path = [{'path': nodes[key]['location']['path'],
                                            'function': definitions[owned[key]]['qualified'],
                                            'callee': references[key]['target'],
                                            'line': nodes[key]['location']['line'],
                                            'caller_usr': owned[key], 'callee_usr': references[key]['target_usr']}
                                           for key in path]
                        raise
                pending.append((call['target'], path))
        checked = []
        for call in calls:
            if call['target'] not in protected:
                continue
            node = nodes[call['key']]
            checked.append({'path': node['location']['path'], 'function': definitions[call['owner']]['qualified'],
                            'input': 'command', 'callee': definitions[call['target']]['qualified'],
                            'consequence': 'representation'})
        # Keep all unresolved indirect/external calls reachable from the
        # controller. Passing the direct rule does not hide such callbacks.
        unresolved = []
        for call in calls:
            if call['owner'] in reached and (call['target'] not in definitions or call['dynamic']):
                node = nodes[call['key']]
                unresolved.append({'path': node['location']['path'], 'function': definitions[call['owner']]['qualified'],
                                   'line': node['location']['line'],
                                   'callee': references.get(call['key'], {}).get('target', ''),
                                   'reason': 'controller_call_effect_unresolved'})
        return {'files': [{'path': path, 'sha256': digest(raw), 'size_bytes': len(raw)}
                          for path, raw in sorted(self.sources.items())],
                'roles': {role: {'usr': usr, 'function': definitions[usr]['qualified']}
                          for role, usr in identities.items()},
                'edges': checked, 'controller_reachable_functions': sorted(reached),
                'unclassified': unresolved, 'source_audit_complete': False}


class CppProbeReadClosure:
    """Reject known adapter-state reads in the native observation closure.

    Follow direct local calls, possible virtual bodies, function references
    and lambda bodies. Exact field declarations preserve identity through
    renamed helpers. External effects and value-flow/order obligations stay
    explicit; this component cannot accept the complete source audit.
    """

    GAME_MODE = 'ACityLiveEvidenceGameMode'
    ACTOR = 'ACityLiveEvidenceActor'
    ROUTING_FIELDS = frozenset(('Domain', 'Witness', 'Launch', 'BindingHash'))
    CANONICAL_FIELDS = frozenset(('CurrentRaw', 'PendingRaw', 'R0Raw', 'CurrentGeneration', 'PendingGeneration'))

    def __init__(self, inventories, source_bytes):
        CppInputFlowGraph(inventories, source_bytes)
        self.records, self.sources = inventories, source_bytes

    def check(self):
        definitions, owned, calls, references, nodes = _cpp_local_call_index(self.records)
        roles = {}
        for role, name, kind in (('probe', 'CollectWorlds', 'FunctionDecl'),
                                 ('wrapper', self.GAME_MODE + '::Observe', 'CXXMethod'),
                                 ('routing', self.GAME_MODE + '::Routing', 'CXXMethod')):
            matches = [usr for usr, node in definitions.items() if node['qualified'] == name and node['kind'] == kind]
            require(len(matches) == 1, 'lcer.source_inventory_invalid')
            roles[role] = matches[0]
        fields, variables = {}, {}
        for node in nodes.values():
            if node['kind'] == 'FieldDecl' and node['usr']:
                fields[node['usr']] = node
            if node['kind'] == 'VarDecl' and node['usr']:
                variables[node['usr']] = node
        game_fields = {usr: node for usr, node in fields.items()
                       if node['qualified'].rsplit('::', 1)[0] == self.GAME_MODE}
        require(self.ROUTING_FIELDS <= {node['name'] for node in game_fields.values()}, 'lcer.source_inventory_invalid')
        actor_record = {usr for usr, node in fields.items() if node['qualified'] == self.ACTOR + '::AcceptedRecordRaw'}
        owner_refs, adjacent = {}, {}
        call_by_key = {call['key']: call for call in calls}
        for key, reference in references.items():
            owner = owned.get(key)
            if owner is None:
                continue
            owner_refs.setdefault(owner, []).append(key)
            target = reference.get('target_usr')
            if target in definitions:
                if reference['kind'] != 'CallExpr':
                    current = key
                    while current in nodes and current not in call_by_key and nodes[current]['kind'] not in CppInputFlowGraph.FUNCTIONS:
                        current = (current[0], nodes[current]['parent'])
                    if current in call_by_key and call_by_key[current]['target'] == target:
                        # The ordinary call below already accounts for its
                        # callee expression; it is not a callback escape.
                        continue
                adjacent.setdefault(owner, set()).add((target, key, reference['kind'] != 'CallExpr'))
        # An external sort/delegate can invoke a lambda without a local
        # CallExpr to its operator. Visit its actual body conservatively.
        for key, node in nodes.items():
            if node['kind'] == 'LambdaExpr':
                target = nodes.get((key[0], node.get('lambda_operator_node')), {}).get('usr')
                if owned.get(key) and target in definitions:
                    adjacent.setdefault(owned[key], set()).add((target, key, True))
        calls_by_owner = {}
        for call in calls:
            calls_by_owner.setdefault(call['owner'], []).append(call)
        pending = [(roles['probe'], 'probe', []), (roles['wrapper'], 'wrapper', [])]
        visited, edges, obligations, field_reads = set(), set(), set(), []
        while pending:
            owner, context, chain = pending.pop(0)
            if (owner, context) in visited:
                continue
            visited.add((owner, context))
            for key in owner_refs.get(owner, ()):
                reference = references[key]; target = reference.get('target_usr')
                if target not in fields:
                    continue
                field = fields[target]; node = nodes[key]
                is_game = target in game_fields
                permitted_routing = is_game and context == 'routing' and field['name'] in self.ROUTING_FIELDS
                if (is_game and not permitted_routing) or target in actor_record:
                    if field['name'] in self.CANONICAL_FIELDS or target in actor_record:
                        input_kind = 'canonical'
                    elif field['name'] in self.ROUTING_FIELDS or field['name'] in ('Binding', 'StartupRecord'):
                        input_kind = 'binding'
                    elif field['name'] in ('Anchor', 'Resource'):
                        input_kind = 'world'
                    else:
                        input_kind = 'command'
                    error = SourceInputForbidden(node['location']['path'], definitions[owner]['qualified'],
                                                 field['qualified'], node['location']['line'], input_kind)
                    error.compiler_identity = {'function_usr': owner, 'field_usr': target}
                    error.call_path = [{'path': nodes[item]['location']['path'],
                                        'function': definitions[owned[item]]['qualified'],
                                        'callee': references.get(item, {}).get('target', nodes[item]['name']),
                                        'line': nodes[item]['location']['line']} for item in chain]
                    raise error
                field_reads.append({'path': node['location']['path'], 'function': definitions[owner]['qualified'],
                                    'field': field['qualified'], 'field_usr': target, 'context': context,
                                    'line': node['location']['line']})
                # Exact Actor slots are physical observations. Other receiver
                # fields need their separate API/storage provenance summaries.
                if field['qualified'].rsplit('::', 1)[0] == self.ACTOR:
                    edges.add((node['location']['path'], definitions[owner]['qualified'], 'world',
                               field['qualified'], 'observation'))
                elif permitted_routing:
                    edges.add((node['location']['path'], definitions[owner]['qualified'], 'binding',
                               field['qualified'], 'provenance'))
                else:
                    obligations.add((key, context, 'probe_field_receiver_origin_unresolved'))
            for target, key, possible in sorted(adjacent.get(owner, ())):
                next_context = context
                if target == roles['probe']:
                    next_context = 'probe'
                elif target == roles['routing'] and context == 'wrapper':
                    next_context = 'routing'
                    obligations.add((key, context, 'probe_wrapper_routing_order_and_use_unresolved'))
                if possible:
                    obligations.add((key, context, 'probe_possible_callback_invocation_unresolved'))
                pending.append((target, next_context, chain + [key]))
            for call in calls_by_owner.get(owner, ()):
                if call['dynamic'] or call['target'] not in definitions:
                    obligations.add((call['key'], context, 'probe_external_or_dynamic_call_effect_unresolved'))
            for key, reference in ((key, references[key]) for key in owner_refs.get(owner, ())):
                if reference.get('target_kind') == 'VarDecl':
                    declaration = variables.get(reference.get('target_usr'))
                    if declaration is None or declaration.get('global_storage', True):
                        obligations.add((key, context, 'probe_shared_storage_origin_unresolved'))
        return {'files': [{'path': path, 'sha256': digest(raw), 'size_bytes': len(raw)}
                          for path, raw in sorted(self.sources.items())],
                'roles': roles, 'visited': [{'function': definitions[usr]['qualified'], 'usr': usr, 'context': context}
                                            for usr, context in sorted(visited)],
                'edges': [dict(zip(('path', 'function', 'input', 'callee', 'consequence'), row)) for row in sorted(edges)],
                'field_reads': field_reads,
                'unclassified': [{'path': nodes[key]['location']['path'],
                                  'function': definitions[owned[key]]['qualified'], 'line': nodes[key]['location']['line'],
                                  'context': context, 'reason': reason} for key, context, reason in sorted(obligations)],
                'source_audit_complete': False}


class CppFaultStateWriters:
    """Locate fault writes through local aliases and defined helper calls.

    Compiler identities select fields and owners. Possible aliases accumulate
    monotonically; an uncertain alias cannot erase a prohibited writer.
    Native calls, escaped pointers, shared pointees and stage predicates still
    require their own effect proofs. This does not accept the complete audit.
    """

    OWNERS = {'ACityLiveEvidenceGameMode::ArmedFault': 'ACityLiveEvidenceGameMode::ArmFault',
              'ACityLiveEvidenceGameMode::bFaultConsumed': 'ACityLiveEvidenceGameMode::ConsumeFault'}

    def __init__(self, inventories, source_bytes):
        CppInputFlowGraph(inventories, source_bytes)
        self.records, self.sources = inventories, source_bytes

    def check(self):
        definitions, owned, calls, refs, nodes = _cpp_local_call_index(self.records)
        children = {}
        for key, node in nodes.items():
            children.setdefault((key[0], node['parent']), []).append(key)
        fields, owners = {}, {}
        for name, owner in self.OWNERS.items():
            candidates = {n['usr'] for n in nodes.values() if n['kind'] == 'FieldDecl'
                          and n.get('qualified') == name and n.get('usr')}
            candidates.update(r['target_usr'] for r in refs.values()
                              if r.get('target_kind') == 'FieldDecl' and r.get('target') == name)
            require(len(candidates) == 1, 'lcer.source_inventory_invalid')
            fields[next(iter(candidates))] = name
            matches = [usr for usr, n in definitions.items() if n['qualified'] == owner]
            require(len(matches) == 1, 'lcer.source_inventory_invalid')
            owners[name] = matches[0]
        variables = {n['usr']: (key, n) for key, n in nodes.items()
                     if n['kind'] in ('VarDecl', 'ParmDecl') and n.get('usr')}
        pointer_aliases, reference_aliases = {}, {}
        pointer_returns, reference_returns = {}, {}
        definition_keys = {}
        for key, node in nodes.items():
            if node['kind'] in CppInputFlowGraph.FUNCTIONS and node['definition']:
                require(type(node.get('result_type_kind')) is str and bool(node['result_type_kind']) and
                        node['result_type_kind'] == definitions[node['usr']].get('result_type_kind'),
                        'lcer.source_inventory_invalid')
                definition_keys.setdefault(node['usr'], []).append(key)
        bindings, return_sites = [], []
        for call in calls:
            if call['dynamic'] or call['target'] not in definitions:
                continue
            key = call['key']; cursor = nodes[key]; reference = refs.get(key, {})
            arguments = cursor['arguments']
            for definition_key in definition_keys[call['target']]:
                formals = [child for child in children.get(definition_key, ())
                           if nodes[child]['kind'] == 'ParmDecl']
                offset = int(cursor['name'].startswith('operator') and
                    reference.get('target_kind') == 'CXXMethod' and
                    reference.get('target_method_properties', {}).get('static') is False and
                    len(arguments) == len(formals) + 1)
                if len(arguments) != len(formals) + offset:
                    continue
                for argument, formal in zip(arguments[offset:], formals):
                    ids = argument.get('cursor_nodes', ())
                    if len(ids) == 1 and (key[0], ids[0]) in nodes and nodes[formal].get('usr'):
                        bindings.append((key, (key[0], ids[0]), formal))
        for key, node in nodes.items():
            if node['kind'] == 'ReturnStmt' and owned.get(key) in definitions:
                expressions = [child for child in children.get(key, ())
                               if nodes[child]['kind'].endswith('Expr') or nodes[child]['kind'] in CppInputFlowGraph.EXPRESSIONS]
                if len(expressions) == 1:
                    return_sites.append((key, expressions[0], owned[key]))

        def unwrap(key):
            seen = set()
            while key in nodes and nodes[key]['kind'] in ('UnexposedExpr', 'ParenExpr'):
                require(key not in seen, 'lcer.source_inventory_invalid'); seen.add(key)
                nested = children.get(key, ())
                if len(nested) != 1:
                    break
                key = nested[0]
            return key

        def storage(key):
            key = unwrap(key); node = nodes[key]; nested = children.get(key, ())
            ref = refs.get(key, {}); usr = ref.get('target_usr')
            if usr in fields:
                return {usr}
            if usr in reference_aliases:
                return set(reference_aliases[usr])
            if node['kind'] == 'CallExpr' and not ref.get('dynamic_call'):
                return set(reference_returns.get(usr, ()))
            if node['kind'] == 'UnaryOperator' and node['unary_operator'] == '*' and len(nested) == 1:
                return pointers(nested[0])
            if node['kind'] == 'BinaryOperator' and node['binary_operator'] in ('.*', '->*') and len(nested) == 2:
                return pointers(nested[1])
            if node['kind'] == 'ConditionalOperator' and len(nested) == 3:
                return storage(nested[1]) | storage(nested[2])
            return set()

        def pointers(key):
            key = unwrap(key); node = nodes[key]; nested = children.get(key, ())
            ref = refs.get(key, {})
            if node['kind'] == 'CallExpr' and not ref.get('dynamic_call'):
                return set(pointer_returns.get(ref.get('target_usr'), ()))
            if node['kind'] == 'UnaryOperator' and node['unary_operator'] == '&' and len(nested) == 1:
                return storage(nested[0])
            if node['kind'] == 'ConditionalOperator' and len(nested) == 3:
                return pointers(nested[1]) | pointers(nested[2])
            return set(pointer_aliases.get(refs.get(key, {}).get('target_usr'), ()))

        def add(mapping, usr, values):
            previous = mapping.setdefault(usr, set()); extra = values - previous
            previous.update(extra)
            return bool(extra)

        # Every productive round adds a field to a variable or return slot.
        # Bound that finite monotone domain; recursive calls cannot erase facts.
        for _ in range(2 * len(fields) * (len(variables) + len(definitions)) + 1):
            changed = False
            for usr, (key, node) in variables.items():
                if node['kind'] != 'VarDecl':
                    continue
                initializers = [child for child in children.get(key, ())
                                if nodes[child]['kind'].endswith('Expr') or nodes[child]['kind'] in CppInputFlowGraph.EXPRESSIONS]
                if len(initializers) != 1:
                    continue
                if node['type_kind'] in ('LValueReference', 'RValueReference'):
                    changed |= add(reference_aliases, usr, storage(initializers[0]))
                elif node['type_kind'] in ('Pointer', 'MemberPointer'):
                    changed |= add(pointer_aliases, usr, pointers(initializers[0]))
            for key, node in nodes.items():
                nested = children.get(key, ())
                if node['kind'] == 'BinaryOperator' and node['binary_operator'] == '=' and len(nested) == 2:
                    target = refs.get(unwrap(nested[0]), {}).get('target_usr')
                    if target in variables and variables[target][1]['type_kind'] in ('Pointer', 'MemberPointer'):
                        changed |= add(pointer_aliases, target, pointers(nested[1]))
            for call, actual, formal in bindings:
                parameter = nodes[formal]
                if parameter['type_kind'] in ('LValueReference', 'RValueReference'):
                    changed |= add(reference_aliases, parameter['usr'], storage(actual))
                elif parameter['type_kind'] in ('Pointer', 'MemberPointer'):
                    changed |= add(pointer_aliases, parameter['usr'], pointers(actual))
            for site, expression, owner in return_sites:
                kind = definitions[owner].get('result_type_kind')
                if kind in ('LValueReference', 'RValueReference'):
                    changed |= add(reference_returns, owner, storage(expression))
                elif kind in ('Pointer', 'MemberPointer'):
                    changed |= add(pointer_returns, owner, pointers(expression))
            if not changed:
                break
        else:
            raise ValueError('lcer.source_field_alias_unclassified')
        writes, unknown, references = [], [], []

        def write(key, destinations, operation):
            for usr in sorted(destinations):
                name = fields[usr]; owner = owned.get(key); node = nodes[key]
                function = definitions[owner]['qualified'] if owner in definitions else '<module>'
                if owner != owners[name]:
                    error = SourceInputForbidden(node['location']['path'], function, name,
                        node['location']['line'], 'world' if function.endswith('::RestartPlayer') else 'command')
                    error.compiler_identity = {'caller_usr': owner, 'field_usr': usr, 'allowed_writer_usr': owners[name]}
                    raise error
                writes.append({'path': node['location']['path'], 'function': function, 'input': 'command',
                               'callee': name, 'consequence': 'fault', 'node': list(key),
                               'field_usr': usr, 'caller_usr': owner, 'operation': operation})

        for key, node in nodes.items():
            nested = children.get(key, ())
            if node['kind'] in ('BinaryOperator', 'CompoundAssignOperator') and len(nested) == 2:
                if node['binary_operator'] in ('=', '+=', '-=', '*=', '/=', '%=', '|=', '&=', '^=', '<<=', '>>='):
                    write(key, storage(nested[0]), 'builtin_assignment')
            elif node['kind'] == 'UnaryOperator' and node['unary_operator'] in ('++', '--') and len(nested) == 1:
                write(key, storage(nested[0]), 'builtin_increment')
            reference = refs.get(key, {})
            if reference.get('target_usr') in fields:
                references.append({'node': list(key), 'field_usr': reference['target_usr'],
                                   'path': node['location']['path'], 'line': node['location']['line'],
                                   'owner_usr': owned.get(key)})
            if node['kind'] != 'CallExpr':
                continue
            # Operator syntax reports its object as argument zero. Ordinary
            # method syntax retains the receiver beneath its member reference.
            receiver = None
            params = reference.get('target_parameters', ())
            props = reference.get('target_method_properties', {})
            if reference.get('target_kind') == 'CXXMethod' and props.get('static') is False:
                if len(node['arguments']) == len(params) + 1 and node['name'].startswith('operator'):
                    ids = node['arguments'][0].get('cursor_nodes', ())
                    if len(ids) == 1:
                        receiver = (key[0], ids[0])
                else:
                    member = [child for child in nested if refs.get(unwrap(child), {}).get('target_usr') == reference.get('target_usr')]
                    if len(member) == 1:
                        bases = children.get(unwrap(member[0]), ())
                        if len(bases) == 1:
                            receiver = bases[0]
            destinations = storage(receiver) if receiver in nodes else set()
            if destinations:
                if props.get('const') is False:
                    write(key, destinations, 'possible_native_receiver_write')
                unknown.append({'node': list(key), 'fields': sorted(destinations),
                                'reason': 'native_fault_handle_method_effects_unresolved',
                                'callee_usr': reference.get('target_usr')})
            for argument in node.get('arguments', ()):
                for number in argument.get('cursor_nodes', ()):
                    candidate = (key[0], number)
                    if candidate in nodes and pointers(candidate):
                        unknown.append({'node': list(key), 'fields': sorted(pointers(candidate)),
                                        'reason': 'fault_storage_pointer_escape_unresolved'})
                    if candidate in nodes and storage(candidate):
                        unknown.append({'node': list(key), 'fields': sorted(storage(candidate)),
                                        'reason': 'fault_storage_argument_effects_unresolved'})
        for mapping, reason in ((reference_aliases, 'fault_reference_alias_effects_unresolved'),
                                (pointer_aliases, 'fault_pointer_alias_effects_unresolved')):
            for usr, targets in sorted(mapping.items()):
                if targets:
                    unknown.append({'node': list(variables[usr][0]), 'fields': sorted(targets), 'reason': reason})
        call_aliases, returned_aliases = [], []
        for call, actual, formal in bindings:
            parameter = nodes[formal]; kind = parameter['type_kind']
            targets = storage(actual) if kind in ('LValueReference', 'RValueReference') else pointers(actual) if kind in ('Pointer', 'MemberPointer') else set()
            if targets:
                call_aliases.append({'call_node': list(call), 'argument_node': list(actual),
                    'parameter_node': list(formal), 'parameter_usr': parameter['usr'],
                    'callee_usr': owned[formal], 'fields': sorted(targets)})
                unknown.append({'node': list(call), 'fields': sorted(targets),
                                'reason': 'fault_formal_alias_context_and_lifetime_unresolved'})
        for site, expression, owner in return_sites:
            kind = definitions[owner].get('result_type_kind')
            targets = storage(expression) if kind in ('LValueReference', 'RValueReference') else pointers(expression) if kind in ('Pointer', 'MemberPointer') else set()
            if targets:
                returned_aliases.append({'return_node': list(site), 'expression_node': list(expression),
                    'function_usr': owner, 'result_type_kind': kind, 'fields': sorted(targets)})
                unknown.append({'node': list(site), 'fields': sorted(targets),
                                'reason': 'fault_return_alias_context_and_lifetime_unresolved'})
        require(set(row['field_usr'] for row in writes) == set(fields), 'lcer.source_field_write_unclassified')
        return {'contract': 'cpp_fault_state_writer_ownership.v1', 'fields': fields, 'allowed_writer_usrs': owners,
                'writes': writes, 'references': references,
                'reference_aliases': {u: sorted(v) for u, v in sorted(reference_aliases.items()) if v},
                'pointer_aliases': {u: sorted(v) for u, v in sorted(pointer_aliases.items()) if v},
                'call_aliases': call_aliases, 'returned_aliases': returned_aliases,
                'unclassified': unknown, 'all_field_writers_classified': False,
                'stage_semantics_accepted': False, 'receiver_identity_accepted': False,
                'source_audit_complete': False,
                'remaining_obligations': ['all_translation_units_and_generated_initializers',
                    'unmodeled_alias_and_shared_pointee_effects', 'native_call_and_receiver_effects',
                    'exact_five_hook_stage_predicates_and_one_shot_state']}


class CppFaultReadinessPredicate:
    """Check FaultReady's complete Boolean relation under native API premises.

    Compiler identities bind fields, arguments and JSON outputs. Equality
    closure removes contradictory paths and redundant literal inequalities.
    Native effects, storage lifetime and world ordering remain separate work.
    """

    METHOD = 'ACityLiveEvidenceGameMode::FaultReady'
    MAX_ROWS = 10000

    def __init__(self, inventories, source_bytes):
        CppInputFlowGraph(inventories, source_bytes)
        self.records, self.sources = inventories, source_bytes

    @classmethod
    def _rows(cls, expression, positive=True):
        tag, *args = expression
        if tag == 'constant':
            return [frozenset()] if args[0] == positive else []
        if tag == 'not':
            return cls._rows(args[0], not positive)
        if tag in ('and', 'or'):
            join = (tag == 'and') == positive
            left, right = cls._rows(args[0], positive), cls._rows(args[1], positive)
            require(len(left) * len(right) <= cls.MAX_ROWS, 'lcer.source_predicate_budget_exceeded')
            return [a | b for a in left for b in right] if join else left + right
        require(tag in ('atom', 'equal'), 'lcer.source_predicate_unclassified')
        return [frozenset([(tag, *args, positive)])]

    @classmethod
    def _normal(cls, expression):
        normalized = set()
        for row in cls._rows(expression):
            parents, facts, unequal = {}, {}, []
            def root(term):
                parents.setdefault(term, term)
                if parents[term] != term:
                    parents[term] = root(parents[term])
                return parents[term]
            possible = True
            for item in sorted(row, key=repr):
                if item[0] == 'atom':
                    _, atom, value = item
                    if atom in facts and facts[atom] != value:
                        possible = False
                    facts[atom] = value
                else:
                    _, a, b, equal = item
                    root(a); root(b)
                    if equal:
                        parents[root(a)] = root(b)
                    else:
                        unequal.append((a, b))
            groups = {}
            for term in parents:
                groups.setdefault(root(term), set()).add(term)
            constants = {}
            for representative, terms in groups.items():
                literals = {term for term in terms if term[0] == 'literal'}
                if len(literals) > 1:
                    possible = False
                if literals:
                    constants[representative] = next(iter(literals))
            inequalities = set()
            for a, b in unequal:
                ra, rb = root(a), root(b)
                if ra == rb:
                    possible = False
                elif ra in constants and rb in constants:
                    if constants[ra] == constants[rb]:
                        possible = False
                else:
                    inequalities.add(tuple(sorted((tuple(sorted(groups[ra], key=repr)),
                                                    tuple(sorted(groups[rb], key=repr))), key=repr)))
            if possible:
                normalized.add((tuple(sorted(facts.items(), key=repr)),
                    tuple(sorted((tuple(sorted(g, key=repr)) for g in groups.values() if len(g) > 1), key=repr)),
                    tuple(sorted(inequalities, key=repr))))
        return sorted(normalized, key=repr)

    @staticmethod
    def _all(expressions):
        result = ('constant', True)
        for expression in expressions:
            result = ('and', result, expression)
        return result

    @classmethod
    def _equal(cls, a, b):
        if a[0] == 'choose':
            return ('or', ('and', a[1], cls._equal(a[2], b)),
                    ('and', ('not', a[1]), cls._equal(a[3], b)))
        if b[0] == 'choose':
            return cls._equal(b, a)
        require(a[0] in ('value', 'json', 'literal') and b[0] in ('value', 'json', 'literal'),
                'lcer.source_predicate_unclassified')
        return ('equal', a, b)

    def check(self):
        definitions, owned, calls, refs, nodes = _cpp_local_call_index(self.records)
        keys = [key for key, n in nodes.items() if n['definition'] and
                n['kind'] == 'CXXMethod' and n['qualified'] == self.METHOD]
        require(len(keys) == 1, 'lcer.source_inventory_invalid')
        key = keys[0]; method = nodes[key]; children = {}
        for child, n in nodes.items():
            children.setdefault((child[0], n['parent']), []).append(child)
        env, prefix, getters, native_calls = {}, [], [], []
        current = key
        def reject():
            n = nodes[current]
            error = SourceInputForbidden(n['location']['path'], self.METHOD, self.METHOD,
                                         n['location']['line'], 'command')
            error.compiler_identity = {'function_usr': method['usr'], 'node': list(current)}
            raise error
        def only(items):
            if len(items) != 1:
                reject()
            return items[0]
        def strip(k):
            while nodes[k]['kind'] in ('UnexposedExpr', 'ParenExpr'):
                k = only(children.get(k, ()))
            return k
        def raw(k):
            n = nodes[k]; a, b = n['start'], n['end']
            require(a['path'] == b['path'] and a['path'] in self.sources, 'lcer.source_inventory_invalid')
            return self.sources[a['path']][a['offset']:b['offset']]
        def field(name):
            names = {n['usr'] for n in nodes.values() if n['kind'] == 'FieldDecl' and
                     n['qualified'] == 'ACityLiveEvidenceGameMode::' + name}
            return only(sorted(names))
        fields = {name: field(name) for name in ('bTerminal', 'bFaultConsumed', 'bBound', 'bEmitted',
            'CurrentGeneration', 'PendingGeneration', 'ArmedFault', 'PendingCommand', 'Witness', 'Domain')}
        flags = {fields[name] for name in ('bTerminal', 'bFaultConsumed', 'bBound', 'bEmitted')}
        parameters = [k for k in children.get(key, ()) if nodes[k]['kind'] == 'ParmDecl']
        stage = nodes[only(parameters)]['usr']
        env[stage] = ('value', stage)
        def arguments(k):
            return [(k[0], only(a.get('cursor_nodes', ()))) for a in nodes[k]['arguments']]
        def receiver(k):
            target = refs[k]['target_usr']
            member = only([child for child in children.get(k, ())
                           if refs.get(strip(child), {}).get('target_usr') == target])
            base = strip(only(children.get(strip(member), ())))
            if nodes[base]['kind'] == 'CallExpr' and refs.get(base, {}).get('target') == 'TSharedPtr::operator->':
                native_calls.append({'node': list(base), 'target_usr': refs[base]['target_usr'],
                                     'premise': 'shared_pointer_dereference_and_lifetime'})
                base = strip(only(arguments(base)))
            result = refs.get(base, {}).get('target_usr')
            if result not in (fields['ArmedFault'], fields['PendingCommand']):
                reject()
            return result
        def expression(k):
            nonlocal current
            current = k; k = strip(k); n = nodes[k]; parts = children.get(k, ()); r = refs.get(k, {})
            usr = r.get('target_usr')
            if usr in flags:
                return ('atom', ('field', usr))
            if usr in fields.values():
                return ('value', usr)
            if usr in env:
                if env[usr] is None:
                    reject()
                return env[usr]
            if n['kind'] == 'CXXBoolLiteralExpr':
                require(raw(k) in (b'true', b'false'), 'lcer.source_inventory_invalid')
                return ('constant', raw(k) == b'true')
            if n['kind'] == 'IntegerLiteral':
                return ('literal', 'int', int(raw(k)))
            if n['kind'] == 'StringLiteral':
                if not n['name'].startswith('u"'):
                    reject()
                return ('literal', 'str', json.loads(n['name'][1:]))
            if n['kind'] == 'UnaryOperator' and n['unary_operator'] == '!':
                return ('not', expression(only(parts)))
            if n['kind'] == 'BinaryOperator' and len(parts) == 2:
                left, right = expression(parts[0]), expression(parts[1]); op = n['binary_operator']
                if op in ('&&', '||'):
                    return ('and' if op == '&&' else 'or', left, right)
                if op in ('==', '!='):
                    equal = self._equal(left, right)
                    return equal if op == '==' else ('not', equal)
                reject()
            if n['kind'] == 'ConditionalOperator' and len(parts) == 3:
                return ('choose', *(expression(p) for p in parts))
            if n['kind'] == 'CallExpr' and not r.get('dynamic_call'):
                args = arguments(k); target = r.get('target')
                native_calls.append({'node': list(k), 'target_usr': r.get('target_usr'),
                                     'premise': 'native_call_effect_and_value_contract'})
                if target in ('FString::FString', 'TStringView::TStringView') and len(args) == 1:
                    return expression(args[0])
                if target == 'CityLCER::Exact' and len(args) == 2:
                    return self._equal(expression(args[0]), expression(args[1]))
                if target == 'TSharedPtr::IsValid' and not args:
                    return ('atom', ('valid', receiver(k)))
                if target == 'FJsonObject::TryGetStringField' and len(args) == 2:
                    object_usr = receiver(k); name = expression(args[0]); output = strip(args[1])
                    output_usr = refs.get(output, {}).get('target_usr')
                    if name[:2] != ('literal', 'str') or output_usr not in env or env[output_usr] is not None:
                        reject()
                    rows = self._normal(self._all(prefix))
                    if not rows or any((('valid', object_usr), True) not in row[0] for row in rows):
                        reject()
                    semantic = (object_usr, name[2])
                    if any(g['object_usr'] == object_usr and g['field'] == name[2] for g in getters):
                        reject()
                    env[output_usr] = ('json', *semantic)
                    getters.append({'node': list(k), 'object_usr': object_usr, 'field': name[2],
                                    'output_usr': output_usr, 'output_node': list(output)})
                    return ('atom', ('read_ok', *semantic))
                reject()
            reject()
        body = only([k for k in children.get(key, ()) if nodes[k]['kind'] == 'CompoundStmt'])
        statements = children.get(body, ()); result = None; guard_nodes = []
        for ordinal, statement in enumerate(statements):
            current = statement; n = nodes[statement]; parts = children.get(statement, ())
            if n['kind'] == 'DeclStmt':
                for declaration in parts:
                    d = nodes[declaration]
                    if d['kind'] != 'VarDecl' or not d['usr']:
                        reject()
                    initializers = [p for p in children.get(declaration, ())
                                    if nodes[p]['kind'].endswith('Expr') or nodes[p]['kind'] in CppInputFlowGraph.EXPRESSIONS]
                    initial = only(initializers); unwrapped = strip(initial)
                    if nodes[unwrapped]['kind'] == 'CallExpr' and refs.get(unwrapped, {}).get('target') == 'FString::FString' and not arguments(unwrapped):
                        env[d['usr']] = None
                        native_calls.append({'node': list(unwrapped), 'target_usr': refs[unwrapped]['target_usr'],
                                             'premise': 'default_string_construction'})
                    else:
                        env[d['usr']] = expression(initial)
            elif n['kind'] == 'IfStmt' and len(parts) == 2:
                condition, terminal = parts
                if nodes[terminal]['kind'] != 'ReturnStmt' or expression(only(children.get(terminal, ()))) != ('constant', False):
                    reject()
                condition_value = expression(condition)
                prefix.append(('not', condition_value)); guard_nodes.append(list(statement))
            elif n['kind'] == 'ReturnStmt' and ordinal == len(statements) - 1:
                result = self._all(prefix + [expression(only(parts))])
            else:
                reject()
        require(result is not None, 'lcer.source_predicate_unclassified')
        expected_reads = {(fields['ArmedFault'], name) for name in ('failure_case', 'stage', 'operation_id')}
        expected_reads.add((fields['PendingCommand'], 'operation_id'))
        if {(g['object_usr'], g['field']) for g in getters} != expected_reads:
            reject()
        atom = lambda *value: ('atom', tuple(value))
        literal = lambda value: ('literal', 'int' if type(value) is int else 'str', value)
        value = lambda name: ('value', fields[name])
        arm = lambda name: ('json', fields['ArmedFault'], name)
        required = [atom('field', fields[name]) if positive else ('not', atom('field', fields[name]))
                    for name, positive in (('bTerminal', False), ('bFaultConsumed', False), ('bBound', True), ('bEmitted', True))]
        required += [self._equal(value(name), literal(1)) for name in ('CurrentGeneration', 'PendingGeneration')]
        required += [atom('valid', fields[name]) for name in ('ArmedFault', 'PendingCommand')]
        required += [atom('read_ok', *item) for item in sorted(expected_reads)]
        required += [self._equal(arm('failure_case'), value('Witness')),
                     self._equal(arm('stage'), ('value', stage)),
                     self._equal(arm('operation_id'), literal('materialize_0002')),
                     self._equal(('json', fields['PendingCommand'], 'operation_id'), arm('operation_id'))]
        expected = ('constant', False)
        contract_raw = (RELEASE_ROOT / CONTRACT_PATH).read_bytes()
        require(digest(contract_raw) == CONTRACT_SHA256, 'lcer.contract_identity_invalid')
        for program in strict_json(contract_raw, canonical=False)['failure_programs']:
            if program['executor'] == 'unreal':
                row = self._all(required + [self._equal(arm('failure_case'), literal(program['id'])),
                    self._equal(value('Domain'), literal(program['domain'])),
                    self._equal(('value', stage), literal(program['stage']))])
                expected = ('or', expected, row)
        actual_rows, expected_rows = self._normal(result), self._normal(expected)
        if actual_rows != expected_rows:
            current = key; reject()
        return {'contract': 'cpp_fault_readiness_predicate.v1', 'function_usr': method['usr'],
                'function_node': list(key), 'guard_nodes': guard_nodes, 'fields': fields, 'stage_usr': stage,
                'json_bindings': getters, 'success_formula': result, 'normalized_success_rows': actual_rows,
                'native_call_premises': native_calls, 'logical_relation_matches_frozen_hooks': True,
                'native_effects_accepted': False, 'field_lifetime_accepted': False,
                'all_stage_semantics_accepted': False, 'source_audit_complete': False,
                'remaining_obligations': ['native_string_json_and_shared_pointer_effects',
                    'field_and_pointee_alias_lifetime_and_concurrency', 'all_field_writers_and_initializers',
                    'arm_dispatch_and_one_shot_mutation_order', 'world_receipt_observation_order']}


class CppSuccessfulCallGuard:
    """Prove direct local sink paths require a successful boolean call.

    This is a bounded structured-control proof. Unknown predicates branch
    both ways. Builtin short-circuit operators preserve evaluation order.
    Data aliases, external effects and sink payload origins are separate
    obligations; this result never accepts the complete source audit.
    """

    def __init__(self, inventories, source_bytes):
        CppInputFlowGraph(inventories, source_bytes)
        self.records = inventories

    def check(self, caller_name, required_name, sink_name):
        return self._check(caller_name, required_name, sink_name, False)

    def check_field_write(self, caller_name, required_name, field_name):
        """Require success before each direct builtin assignment to a field.

        Compiler field identity and the assignment's left operand select the
        writes. Reads and unrelated same-spelled fields are not writes.
        Aliases, overloaded assignment and external mutation effects remain
        separate obligations; this is not complete field-writer authority.
        """
        return self._check(caller_name, required_name, field_name, True)

    def _check(self, caller_name, required_name, sink_name, field_write):
        definitions, owned, calls, references, nodes = _cpp_local_call_index(self.records)
        children = {}
        for key, node in nodes.items():
            children.setdefault((key[0], node['parent']), []).append(key)
        identities = {}
        for name in (caller_name, required_name) + (() if field_write else (sink_name,)):
            matches = [usr for usr, node in definitions.items() if node['qualified'] == name]
            require(len(matches) == 1, 'lcer.source_inventory_invalid')
            identities[name] = matches[0]
        caller = identities[caller_name]
        required = [row['key'] for row in calls if row['owner'] == caller and row['target'] == identities[required_name]]
        if field_write:
            fields = {row['target_usr'] for row in references.values()
                      if row.get('target_kind') == 'FieldDecl' and row.get('target') == sink_name}
            fields.update(node['usr'] for node in nodes.values() if node['kind'] == 'FieldDecl'
                          and node.get('qualified') == sink_name and node.get('usr'))
            require(len(fields) == 1, 'lcer.source_inventory_invalid')
            identities[sink_name] = next(iter(fields))
            sinks = set()
            for key, reference in references.items():
                if owned.get(key) != caller or reference.get('target_usr') != identities[sink_name]:
                    continue
                left = key
                parent = (left[0], nodes[left]['parent'])
                while parent in nodes and nodes[parent]['kind'] in ('UnexposedExpr', 'ParenExpr'):
                    require(children.get(parent) == [left], 'lcer.source_field_write_unclassified')
                    left, parent = parent, (parent[0], nodes[parent]['parent'])
                if (parent in nodes and nodes[parent]['kind'] == 'BinaryOperator'
                        and nodes[parent]['binary_operator'] == '='
                        and children.get(parent, [None])[0] == left):
                    sinks.add(parent)
            # A read-only use or aliased write cannot produce an empty proof.
            require(bool(sinks), 'lcer.source_field_write_unclassified')
            sinks = sorted(sinks)
        else:
            sinks = [row['key'] for row in calls if row['owner'] == caller and row['target'] == identities[sink_name]]
            require(bool(sinks), 'lcer.source_inventory_invalid')

        def reject(key):
            node = nodes[key]
            error = SourceInputForbidden(node['location']['path'], caller_name, sink_name,
                                         node['location']['line'], 'command')
            error.compiler_identity = {'caller_usr': caller, 'required_usr': identities[required_name],
                                       'sink_usr': identities[sink_name]}
            raise error

        # A missing call is a failed proof, not an empty successful case set.
        if not required:
            reject(sinks[0])
        for key, node in nodes.items():
            if owned.get(key) == caller and node['kind'] in (
                    'GotoStmt', 'IndirectGotoStmt', 'LabelStmt', 'AddrLabelExpr',
                    'CXXTryStmt', 'CXXCatchStmt', 'SEHTryStmt'):
                raise ValueError('lcer.source_control_flow_unclassified')

        def ancestors(key):
            result = []
            while key in nodes:
                result.append(key)
                key = (key[0], nodes[key]['parent'])
            return result

        # Analyze the smallest real compound containing both call and sink.
        # Starting with no successful call is conservative for all entries.
        reports = []
        for sink in sinks:
            sink_ancestors = ancestors(sink)
            call_ancestors = {key: set(ancestors(key)) for key in required}
            scopes = [key for key in sink_ancestors if nodes[key]['kind'] == 'CompoundStmt'
                      and any(key in parents for parents in call_ancestors.values())]
            require(bool(scopes), 'lcer.source_control_flow_unclassified')
            scope = scopes[0]
            local_required = [key for key, parents in call_ancestors.items() if scope in parents]
            require(len(local_required) == 1, 'lcer.source_control_flow_unclassified')
            required_key = local_required[0]
            contains_cache = {}
            reached = set()

            def contains(key, target):
                pair = (key, target)
                if pair not in contains_cache:
                    contains_cache[pair] = key == target or any(contains(child, target) for child in children.get(key, ()))
                return contains_cache[pair]

            def boolean(key, states):
                node, nested = nodes[key], children.get(key, ())
                if key == required_key:
                    return {(True, True), (False, False)} if states else set()
                if key == sink:
                    reached.update(states)
                    return {(truth, state) for state in states for truth in (True, False)}
                if not contains(key, required_key) and not contains(key, sink):
                    return {(truth, state) for state in states for truth in (True, False)}
                if node['kind'] in ('UnexposedExpr', 'ParenExpr') and len(nested) == 1:
                    return boolean(nested[0], states)
                if node['kind'] == 'UnaryOperator' and node['unary_operator'] == '!' and len(nested) == 1:
                    return {(not truth, state) for truth, state in boolean(nested[0], states)}
                if node['kind'] == 'BinaryOperator' and node['binary_operator'] in ('&&', '||') and len(nested) == 2:
                    result = set()
                    for truth, state in boolean(nested[0], states):
                        if truth == (node['binary_operator'] == '||'):
                            result.add((truth, state))
                        else:
                            result.update(boolean(nested[1], {state}))
                    return result
                raise ValueError('lcer.source_control_flow_unclassified')

            def statement(key, states):
                if not states:
                    return set()
                node, nested = nodes[key], children.get(key, ())
                if node['kind'] == 'CompoundStmt':
                    for child in nested:
                        states = statement(child, states)
                    return states
                if node['kind'] == 'IfStmt':
                    require(len(nested) in (2, 3), 'lcer.source_control_flow_unclassified')
                    outcomes = boolean(nested[0], states)
                    positive = {state for truth, state in outcomes if truth}
                    negative = {state for truth, state in outcomes if not truth}
                    return statement(nested[1], positive) | (statement(nested[2], negative) if len(nested) == 3 else negative)
                if node['kind'] == 'ReturnStmt':
                    require(not contains(key, required_key) and not contains(key, sink), 'lcer.source_control_flow_unclassified')
                    return set()
                if node['kind'] in ('ForStmt', 'WhileStmt', 'DoStmt', 'CXXForRangeStmt', 'SwitchStmt',
                                    'CaseStmt', 'DefaultStmt', 'BreakStmt', 'ContinueStmt'):
                    raise ValueError('lcer.source_control_flow_unclassified')
                if contains(key, required_key):
                    raise ValueError('lcer.source_control_flow_unclassified')
                if contains(key, sink):
                    # A sink nested in a conditional expression, lambda or
                    # callback needs its own evaluation semantics.
                    cursor = sink
                    while cursor != key:
                        cursor = (cursor[0], nodes[cursor]['parent'])
                        require(nodes[cursor]['kind'] in ('CallExpr', 'UnexposedExpr', 'ParenExpr'),
                                'lcer.source_control_flow_unclassified')
                    reached.update(states)
                return states

            statement(scope, {None})
            if reached != {True}:
                reject(sink)
            reports.append({'path': nodes[sink]['location']['path'], 'function': caller_name,
                            'required_call': required_name, 'callee': sink_name,
                            'required_call_node': list(required_key), 'sink_node': list(sink),
                            'scope_node': list(scope), 'sink_states': ['required_call_returned_true']})
        result = {'guards': reports, 'source_audit_complete': False,
                  'remaining_obligations': ['external_call_effects', 'sink_payload_origin_and_alias_writes',
                                            'callee_success_and_world_semantics']}
        if field_write:
            result.update(sink_kind='direct_builtin_field_assignment', field_usr=identities[sink_name],
                          all_field_writers_classified=False, receiver_identity_accepted=False)
            result['remaining_obligations'].extend(['field_alias_and_overloaded_assignment_writers',
                                                   'field_receiver_identity', 'required_call_stage_semantics'])
        return result


class PythonReturnFlow:
    """Conservative normal-return exits; no expression or candidate executes.

    Expressions may raise. Branches and zero-iteration loops remain possible.
    Exception matching is conservative. finally overrides earlier exits, and
    a context manager may suppress a body exception. These return-path rules
    do not discharge truth, iteration, exception or context-manager effects.
    """

    NORMAL = ('normal', ())
    RAISE = ('raise', ())
    BREAK = ('break', ())
    CONTINUE = ('continue', ())

    def __init__(self):
        self.unsupported = set()

    def _block(self, body):
        exits = {self.NORMAL}
        for statement in body:
            if self.NORMAL not in exits:
                break
            exits.remove(self.NORMAL)
            exits.update(self._statement(statement))
        return exits

    def _statement(self, node):
        if isinstance(node, ast.Return):
            return {('return', (node.lineno, node.col_offset)), self.RAISE}
        if isinstance(node, ast.Raise):
            return {self.RAISE}
        if isinstance(node, ast.Break):
            return {self.BREAK}
        if isinstance(node, ast.Continue):
            return {self.CONTINUE}
        if isinstance(node, (ast.Pass, ast.Global, ast.Nonlocal)):
            return {self.NORMAL}
        if isinstance(node, ast.If):
            return self._block(node.body) | self._block(node.orelse) | {self.RAISE}
        if isinstance(node, (ast.For, ast.While)):
            body = self._block(node.body)
            exits = (body - {self.NORMAL, self.BREAK, self.CONTINUE}) | self._block(node.orelse) | {self.RAISE}
            if self.BREAK in body:
                exits.add(self.NORMAL)
            return exits
        if isinstance(node, ast.With):
            body = self._block(node.body)
            exits = body | {self.RAISE}
            if self.RAISE in body or len(node.items) > 1:
                exits.add(self.NORMAL)
            return exits
        if isinstance(node, ast.Try):
            body = self._block(node.body)
            exits = body - {self.NORMAL}
            if self.NORMAL in body:
                exits.update(self._block(node.orelse))
            if self.RAISE in body:
                for handler in node.handlers:
                    exits.update(self._block(handler.body))
            final = self._block(node.finalbody)
            return (exits if self.NORMAL in final else set()) | (final - {self.NORMAL})
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Assert,
                             ast.Delete, ast.Import, ast.ImportFrom, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            return {self.NORMAL, self.RAISE}
        self.unsupported.add(type(node).__name__)
        return {self.NORMAL, self.RAISE}

    def analyze(self, syntax):
        suspension = []
        class Suspension(ast.NodeVisitor):
            def visit_Yield(visitor, node):
                suspension.append('yield')
            visit_YieldFrom = visit_Yield
            def visit_FunctionDef(visitor, node):
                # Defaults and decorators execute in the enclosing scope;
                # the nested function body does not. Keep this distinction
                # even for a yield in an otherwise unreachable default.
                for value in [*node.decorator_list, *node.args.defaults,
                              *(item for item in node.args.kw_defaults if item is not None)]:
                    visitor.visit(value)
                for argument in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
                                 *(item for item in (node.args.vararg, node.args.kwarg) if item is not None)]:
                    if argument.annotation is not None:
                        visitor.visit(argument.annotation)
                if node.returns is not None:
                    visitor.visit(node.returns)
            visit_AsyncFunctionDef = visit_FunctionDef
            def visit_ClassDef(visitor, node):
                for value in [*node.decorator_list, *node.bases, *(item.value for item in node.keywords)]:
                    visitor.visit(value)
            def visit_Lambda(visitor, node):
                for value in [*node.args.defaults, *(item for item in node.args.kw_defaults if item is not None)]:
                    visitor.visit(value)
        visitor = Suspension()
        if isinstance(syntax, ast.Lambda):
            visitor.visit(syntax.body)
            exits = {('return', (syntax.lineno, syntax.col_offset)), self.RAISE}
        else:
            for statement in syntax.body:
                visitor.visit(statement)
            exits = self._block(syntax.body)
        deferred = ('async_generator' if suspension else 'coroutine') if isinstance(syntax, ast.AsyncFunctionDef) else (
            'generator' if suspension else None)
        if self.BREAK in exits or self.CONTINUE in exits:
            self.unsupported.add('unbound_loop_exit')
        return {'return_sites': [list(site) for kind, site in sorted(exits) if kind == 'return'],
                'falls_through': self.NORMAL in exits, 'may_raise': self.RAISE in exits,
                'suspension': deferred, 'unsupported': sorted(self.unsupported),
                'supported': not self.unsupported}


class PythonSuccessfulTypeGuards:
    """Conditional exact types on structured successful paths.

    This consumes closed callable facts, never a function's spelling. Local
    stores kill a fact. Joins retain only names guarded on every normal path.
    Exceptions, finally, loops and context suppression cannot borrow a guard
    from a different path. Opaque mutation and binding authority stay open.
    """

    BUILTIN_TYPES = {'bool', 'int', 'float', 'complex', 'str', 'bytes', 'bytearray',
                     'list', 'tuple', 'dict', 'set', 'frozenset', 'range'}

    def __init__(self, graph, facts):
        self.graph, self.facts = graph, facts
        self.index, self.reads = {}, {}
        for node in graph.nodes:
            key = (node['path'], node['function'], node['line'], node['column'], node['kind'])
            self.index.setdefault(key, []).append(node['id'])
        self.calls = {call['node']: call for call in graph.calls}
        self.helper_cache = {}

    def _node(self, syntax):
        kind = 'name_read' if isinstance(syntax, ast.Name) else type(syntax).__name__
        key = (self.scope['path'], self.scope['name'], getattr(syntax, 'lineno', 0),
               getattr(syntax, 'col_offset', 0), kind)
        nodes = self.index.get(key, ())
        if len(nodes) > 1 and isinstance(syntax, ast.Call):
            # Nested calls can share their start position. Their complete
            # parsed expression must agree before a producer is selected.
            nodes = [number for number in nodes if self.graph.nodes[number]['label'] == ast.unparse(syntax)]
        return nodes[0] if len(nodes) == 1 else None

    @staticmethod
    def _merge(states):
        states = [state for state in states if state is not None]
        if not states:
            return None
        common = set(states[0]).intersection(*(set(state) for state in states[1:]))
        return {name: {field: frozenset().union(*(state[name][field] for state in states))
                       for field in ('types', 'inputs', 'guards', 'preconditions')}
                for name in common}

    @staticmethod
    def _walrus_names(syntax):
        return {node.target.id for node in ast.walk(syntax)
                if isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name)}

    def _expression(self, syntax, state):
        # Kill all assignment-expression targets before inspecting any part.
        # This intentionally loses precision when execution order is unknown.
        state = {name: fact for name, fact in state.items() if name not in self._walrus_names(syntax)}
        owner = self
        class Reads(ast.NodeVisitor):
            def visit_Name(visitor, node):
                if isinstance(node.ctx, ast.Load):
                    number = owner._node(node)
                    if number is not None:
                        observed = {node.id: state[node.id]} if node.id in state else {}
                        previous = owner.reads.get(number)
                        owner.reads[number] = observed if previous is None else owner._merge([previous, observed])
            def visit_Lambda(visitor, node):
                pass
            def visit_ListComp(visitor, node):
                pass
            visit_SetComp = visit_ListComp
            visit_DictComp = visit_ListComp
            visit_GeneratorExp = visit_ListComp
        Reads().visit(syntax)
        return state

    def _predicate(self, syntax, truth, extra=()):
        if self._walrus_names(syntax):
            return {}
        if isinstance(syntax, ast.UnaryOp) and isinstance(syntax.op, ast.Not):
            return self._predicate(syntax.operand, not truth, extra)
        if isinstance(syntax, ast.BoolOp) and ((isinstance(syntax.op, ast.And) and truth)
                                                or (isinstance(syntax.op, ast.Or) and not truth)):
            result = {}
            for value in syntax.values:
                result.update(self._predicate(value, truth, extra))
            return result
        if not isinstance(syntax, ast.Compare) or len(syntax.ops) != 1:
            return {}
        if not ((isinstance(syntax.ops[0], ast.Is) and truth)
                or (isinstance(syntax.ops[0], ast.IsNot) and not truth)):
            return {}
        for value, expected in ((syntax.left, syntax.comparators[0]), (syntax.comparators[0], syntax.left)):
            if not isinstance(value, ast.Call) or len(value.args) != 1 or value.keywords or not isinstance(value.args[0], ast.Name):
                continue
            name = value.args[0].id
            if name not in self.scope['locals']:
                continue
            call_node, class_node, predicate_node = self._node(value), self._node(expected), self._node(syntax)
            call = self.calls.get(call_node)
            if call is None or self.facts.get(call['function']) != {'external:builtins.type'}:
                continue
            targets = self.facts.get(class_node, set())
            if len(targets) != 1:
                continue
            target = next(iter(targets))
            if target not in {'external:builtins.' + item for item in self.BUILTIN_TYPES}:
                continue
            typename = target[len('external:builtins.'):]
            if predicate_node is None:
                continue
            conditions = {'authentic_builtin_binding:type', 'authentic_builtin_binding:' + typename,
                          'guarded_local_binding_stable_during_and_after_check:' + self.identity + ':' + name, *extra}
            return {name: {'types': frozenset({typename}),
                           'inputs': frozenset({call_node, class_node, predicate_node}),
                           'guards': frozenset({predicate_node}), 'preconditions': frozenset(conditions)}}
        return {}

    def _helper(self, identity):
        if identity in self.helper_cache:
            return self.helper_cache[identity]
        definition = self.graph.definitions[identity]
        syntax = self.graph.scopes[definition['scope']]['tree']
        result = None
        if isinstance(syntax, ast.FunctionDef):
            body = syntax.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                body = body[1:]
            if (len(body) == 1 and isinstance(body[0], ast.If) and not body[0].orelse
                    and len(body[0].body) == 1 and isinstance(body[0].body[0], ast.Raise)):
                test, required = body[0].test, False
                if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
                    test, required = test.operand, True
                if isinstance(test, ast.Name):
                    names = [arg.arg for arg in [*syntax.args.posonlyargs, *syntax.args.args, *syntax.args.kwonlyargs]]
                    if test.id in names:
                        result = (syntax, test.id, required)
        self.helper_cache[identity] = result
        return result

    def _guard_call(self, syntax):
        if not isinstance(syntax, ast.Call) or self._walrus_names(syntax):
            return {}
        if any(isinstance(arg, ast.Starred) for arg in syntax.args) or any(item.arg is None for item in syntax.keywords):
            return {}
        node = self._node(syntax)
        call = self.calls.get(node)
        targets = self.facts.get(call['function'], set()) if call else set()
        if not targets or any(not target.startswith('function:') for target in targets):
            return {}
        keywords = {item.arg: item.value for item in syntax.keywords}
        if len(keywords) != len(syntax.keywords):
            return {}
        alternatives = []
        for target in sorted(targets):
            identity = target[len('function:'):]
            helper = self._helper(identity)
            if helper is None:
                return {}
            definition, condition, required = helper
            positional = [arg.arg for arg in [*definition.args.posonlyargs, *definition.args.args]]
            if condition in positional and positional.index(condition) < len(syntax.args):
                if condition in keywords:
                    return {}
                argument = syntax.args[positional.index(condition)]
            elif condition in keywords and condition not in {arg.arg for arg in definition.args.posonlyargs}:
                argument = keywords[condition]
            else:
                return {}
            facts = self._predicate(argument, required, ('authentic_guard_callable_body:' + identity,
                                                        'guard_callable_body_stable_during_call:' + identity))
            for fact in facts.values():
                fact['inputs'] |= frozenset({node, self.graph.definitions[identity]['node']})
                fact['guards'] |= frozenset({node})
            alternatives.append(facts)
        return self._merge(alternatives) or {}

    def _block(self, body, state):
        state = dict(state)
        for statement in body:
            if state is None:
                break
            state = self._statement(statement, state)
        return state

    def _statement(self, node, state):
        if isinstance(node, ast.If):
            state = self._expression(node.test, state)
            positive = {**state, **self._predicate(node.test, True)}
            negative = {**state, **self._predicate(node.test, False)}
            return self._merge([self._block(node.body, positive), self._block(node.orelse, negative)])
        if isinstance(node, ast.Expr):
            state = self._expression(node.value, state)
            return {**state, **self._guard_call(node.value)}
        if isinstance(node, (ast.Return, ast.Raise)):
            for value in ast.iter_child_nodes(node):
                if isinstance(value, ast.expr):
                    state = self._expression(value, state)
            return None
        if isinstance(node, (ast.Break, ast.Continue)):
            return None
        if isinstance(node, ast.Try):
            normal = self._block(node.body, state)
            if normal is not None:
                normal = self._block(node.orelse, normal)
            outcomes = [normal, *(self._block(handler.body, {}) for handler in node.handlers)]
            merged = self._merge(outcomes)
            # finally can also run for pending exceptions and returns. Do not
            # lend it guards that only hold on the normal path through try.
            final = self._block(node.finalbody, {}) if node.finalbody else None
            return (final if merged is not None and final is not None else None) if node.finalbody else merged
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            self._expression(node.iter if isinstance(node, (ast.For, ast.AsyncFor)) else node.test, state)
            self._block(node.body, {})
            self._block(node.orelse, {})
            return {}
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                self._expression(item.context_expr, state)
            self._block(node.body, {})
            return {}
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete)):
            if getattr(node, 'value', None) is not None:
                state = self._expression(node.value, state)
            targets = node.targets if isinstance(node, (ast.Assign, ast.Delete)) else [node.target]
            killed = {part.id for target in targets for part in ast.walk(target)
                      if isinstance(part, ast.Name) and isinstance(part.ctx, (ast.Store, ast.Del))}
            return {name: fact for name, fact in state.items() if name not in killed}
        if isinstance(node, ast.Assert):
            # Assertions may be compiled out. They never introduce a fact.
            return self._expression(node.test, state)
        if isinstance(node, ast.Pass):
            return state
        # Imports, definitions, unsupported control and binding forms cannot
        # carry a prior local-name constraint through this bounded analyzer.
        return {}

    def analyze(self):
        for identity, definition in sorted(self.graph.definitions.items()):
            scope = self.graph.scopes[definition['scope']]
            if definition['kind'] != 'function' or not isinstance(scope['tree'], ast.FunctionDef):
                continue
            self.identity, self.scope = identity, scope
            self._block(scope['tree'].body, {})
        records = []
        for number, names in sorted(self.reads.items()):
            for name, fact in sorted(names.items()):
                records.append({'contract': 'python_successful_type_guard.v1', 'node': number, 'name': name,
                                'output_types': sorted(fact['types']), 'inputs': sorted(fact['inputs']),
                                'possible_guard_nodes': sorted(fact['guards']),
                                'preconditions': sorted(fact['preconditions']),
                                'classification': 'conditional_successful_path'})
        return records


class PythonSuccessfulLocalTypes(PythonSuccessfulTypeGuards):
    """Source-derived assignment types at particular successful local reads.

    A shared symbol's other assignments do not replace the producer active
    on this path. Unresolved RHS values kill the prior fact. The inherited
    control walker keeps all normal alternatives and refuses to lend a
    normal-path fact to exception, loop or context-manager exits.
    """

    @staticmethod
    def _merge(states):
        states = [state for state in states if state is not None]
        if not states:
            return None
        common = set(states[0]).intersection(*(set(state) for state in states[1:]))
        return {name: {field: frozenset().union(*(state[name].get(field, ()) for state in states))
                       for field in ('types', 'inputs', 'guards', 'preconditions', 'assignments')}
                for name in common}

    def _statement(self, node, state):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or getattr(node, 'value', None) is None:
            return super()._statement(node, state)
        state = self._expression(node.value, state)
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        killed = {part.id for target in targets for part in ast.walk(target)
                  if isinstance(part, ast.Name) and isinstance(part.ctx, ast.Store)}
        result = {name: fact for name, fact in state.items() if name not in killed}
        # Tuple unpacking, descriptors, subscripts and nonlocal/global stores
        # require their own transfer contracts. Do not guess their effects.
        if not all(isinstance(target, ast.Name) and target.id in self.scope['locals'] for target in targets):
            return result
        source = self._node(node.value)
        if source is None:
            return result
        inherited = state.get(node.value.id) if isinstance(node.value, ast.Name) else None
        values = self.facts.get(source, set())
        if inherited is not None:
            fact = {field: inherited.get(field, frozenset())
                    for field in ('types', 'inputs', 'guards', 'preconditions', 'assignments')}
        elif values and all(value.startswith('type:') for value in values):
            fact = {'types': frozenset(value[len('type:'):] for value in values),
                    'inputs': frozenset(), 'guards': frozenset(),
                    'preconditions': frozenset(), 'assignments': frozenset()}
        else:
            return result
        for target in targets:
            assignments = []
            for kind in ('assignment_value', 'controlled_assignment'):
                assignments.extend(self.index.get((self.scope['path'], self.scope['name'],
                                                   target.lineno, target.col_offset, kind), ()))
            if len(assignments) != 1:
                continue
            result[target.id] = {**fact, 'inputs': fact['inputs'] | frozenset({source}),
                                 'assignments': fact['assignments'] | frozenset(assignments),
                                 'preconditions': fact['preconditions'] | frozenset({
                                     'parsed_local_callable_body:' + self.identity,
                                     'successful_local_assignment_binding_stable:' + self.identity + ':' + target.id})}
        return result

    def analyze(self):
        super().analyze()
        records = []
        for number, names in sorted(self.reads.items()):
            for name, fact in sorted(names.items()):
                if not fact.get('assignments'):
                    continue
                records.append({'contract': 'python_successful_local_type.v1', 'node': number, 'name': name,
                                'output_types': sorted(fact['types']), 'inputs': sorted(fact['inputs']),
                                'assignment_nodes': sorted(fact['assignments']),
                                'possible_guard_nodes': sorted(fact['guards']),
                                'preconditions': sorted(fact['preconditions']),
                                'classification': 'conditional_successful_assignment'})
        return records


class PythonJsonDecodedMembers(PythonSuccessfulTypeGuards):
    """Conditional recursive member construction, separate from callback effects.

    A callback returning a dict does not prove its nested values. Recognize
    the actual pair-forwarding body and scalar conversions, and retain all
    binding, callback and reachable-member mutation obligations.
    """

    def __init__(self, graph, facts):
        super().__init__(graph, facts)
        # The primitive result-fact table omits external APIs without a
        # primitive summary. Preserve their actual source-bound references;
        # a spelling or a matching return type cannot identify the callee.
        self.binding_references = graph._references()

    @staticmethod
    def _source(node):
        return {'line': node.lineno, 'column': node.col_offset,
                'end_line': node.end_lineno, 'end_column': node.end_col_offset}

    @staticmethod
    def _body(syntax):
        body = syntax.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and type(body[0].value.value) is str:
            body = body[1:]
        return body

    def _native_call(self, node, target, argument):
        number = self._node(node)
        call = self.calls.get(number)
        return (isinstance(node, ast.Call) and len(node.args) == 1 and not node.keywords and
                isinstance(node.args[0], ast.Name) and node.args[0].id == argument and
                call is not None and self.binding_references.get(call['function']) == {('external', target, '')})

    def _successful_guard(self, statement):
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            return None
        syntax = statement.value
        if syntax.keywords or any(isinstance(n, ast.Starred) for n in syntax.args):
            return None
        call = self.calls.get(self._node(syntax))
        targets = self.facts.get(call['function'], set()) if call else set()
        if len(targets) != 1 or not next(iter(targets)).startswith('function:'):
            return None
        identity = next(iter(targets))[len('function:'):]
        helper = self._helper(identity)
        if helper is None or helper[2] is not True:
            return None
        declaration, predicate, _ = helper
        args = declaration.args
        names = [n.arg for n in [*args.posonlyargs, *args.args]]
        if (args.vararg or args.kwarg or args.kwonlyargs or len(syntax.args) > len(names) or
                len(syntax.args) < len(names) - len(args.defaults) or predicate not in names):
            return None
        index = names.index(predicate)
        if index >= len(syntax.args) or any(not isinstance(n, ast.Constant) or type(n.value) not in
                                          (str, int, bool, type(None)) for i, n in enumerate(syntax.args) if i != index):
            return None
        return {'predicate': syntax.args[index], 'function': identity,
                'call_source': self._source(syntax), 'body_source': self._source(declaration)}

    def _callback(self, identity, hook, never_returns):
        definition = self.graph.definitions[identity]
        self.scope = self.graph.scopes[definition['scope']]
        self.identity = identity
        syntax = self.scope['tree']
        record = {'function': identity, 'hook': hook, 'source': self._source(syntax),
                  'recursive_construction_supported': False, 'kind': 'unresolved',
                  'preconditions': ['json_member_callback_identity_and_body_stable:' + identity],
                  'callback_effects_accepted': False}
        if never_returns:
            record.update(kind='no_successful_callback_return', recursive_construction_supported=True,
                          output_types=[])
            return record
        if not isinstance(syntax, ast.FunctionDef) or syntax.decorator_list:
            return record
        args = syntax.args
        parameters = [*args.posonlyargs, *args.args]
        if len(parameters) != 1 or args.defaults or args.kwonlyargs or args.vararg or args.kwarg:
            return record
        argument = parameters[0].arg
        body = self._body(syntax)
        if hook == 'object_hook' and len(body) == 1 and isinstance(body[0], ast.Return) and isinstance(body[0].value, ast.Name) and body[0].value.id == argument:
            record.update(kind='native_object_identity', recursive_construction_supported=True,
                          input_parameter=argument, return_source=self._source(body[0]), output_types=['dict'])
            return record
        if hook == 'object_pairs_hook' and len(body) == 3:
            initial, loop, returned = body
            if not (isinstance(initial, ast.Assign) and len(initial.targets) == 1 and isinstance(initial.targets[0], ast.Name) and
                    isinstance(initial.value, ast.Dict) and not initial.value.keys and isinstance(loop, ast.For) and
                    isinstance(loop.iter, ast.Name) and loop.iter.id == argument and isinstance(loop.target, ast.Tuple) and
                    len(loop.target.elts) == 2 and all(isinstance(n, ast.Name) for n in loop.target.elts) and
                    not loop.orelse and len(loop.body) == 2 and isinstance(returned, ast.Return) and isinstance(returned.value, ast.Name)):
                return record
            container = initial.targets[0].id
            key, item = [n.id for n in loop.target.elts]
            if len({argument, container, key, item}) != 4 or returned.value.id != container:
                return record
            guard, assignment = loop.body
            if not (isinstance(assignment, ast.Assign) and len(assignment.targets) == 1 and isinstance(assignment.targets[0], ast.Subscript) and
                    isinstance(assignment.targets[0].value, ast.Name) and assignment.targets[0].value.id == container and
                    isinstance(assignment.targets[0].slice, ast.Name) and assignment.targets[0].slice.id == key and
                    isinstance(assignment.value, ast.Name) and assignment.value.id == item):
                return record
            guard_record = None
            if isinstance(guard, ast.If) and not guard.orelse and len(guard.body) == 1 and isinstance(guard.body[0], ast.Raise):
                predicate, expected = guard.test, ast.In
                guard_record = {'kind': 'duplicate_raises', 'source': self._source(guard)}
            else:
                helper = self._successful_guard(guard)
                if helper is None:
                    return record
                predicate, expected = helper['predicate'], ast.NotIn
                guard_record = {'kind': 'successful_duplicate_guard', **{k: v for k, v in helper.items() if k != 'predicate'}}
                record['preconditions'].append('json_member_guard_identity_and_body_stable:' + helper['function'])
            if not (isinstance(predicate, ast.Compare) and len(predicate.ops) == 1 and isinstance(predicate.ops[0], expected) and
                    isinstance(predicate.left, ast.Name) and predicate.left.id == key and
                    isinstance(predicate.comparators[0], ast.Name) and predicate.comparators[0].id == container):
                return record
            record.update(kind='fresh_dict_forwarding_decoded_pairs', recursive_construction_supported=True,
                          input_parameter=argument, accumulator=container, key_parameter=key, member_parameter=item,
                          initial_source=self._source(initial), loop_source=self._source(loop),
                          assignment_source=self._source(assignment), return_source=self._source(returned),
                          guard=guard_record, output_types=['dict'], member_origin='native_decoded_pair_value',
                          key_origin='native_decoded_string', input_members_modified_by_store=False)
            record['preconditions'].extend(['native_json_pairs_are_exact_list_of_exact_pairs',
                                            'native_json_object_keys_are_exact_str',
                                            'json_callback_input_members_already_satisfy_recursive_construction'])
            return record
        if hook in ('parse_int', 'parse_float', 'parse_constant'):
            for typename in ('int', 'float'):
                target = 'builtins.' + typename
                if len(body) == 1 and isinstance(body[0], ast.Return) and self._native_call(body[0].value, target, argument):
                    record.update(kind='native_scalar_conversion', recursive_construction_supported=True,
                                  input_parameter=argument, conversion_source=self._source(body[0].value),
                                  return_source=self._source(body[0]), output_types=[typename])
                    record['preconditions'].append('authentic_builtin_binding:' + typename)
                    return record
                if len(body) != 3:
                    continue
                initial, guard, returned = body
                if not (isinstance(initial, ast.Assign) and len(initial.targets) == 1 and isinstance(initial.targets[0], ast.Name) and
                        self._native_call(initial.value, target, argument) and isinstance(returned, ast.Return) and
                        isinstance(returned.value, ast.Name) and returned.value.id == initial.targets[0].id):
                    continue
                helper = self._successful_guard(guard)
                if helper is None or not self._native_call(helper['predicate'], 'math.isfinite', initial.targets[0].id):
                    continue
                record.update(kind='native_scalar_conversion_with_finite_guard', recursive_construction_supported=True,
                              input_parameter=argument, conversion_source=self._source(initial.value),
                              return_source=self._source(returned), output_types=[typename],
                              guard={k: v for k, v in helper.items() if k != 'predicate'})
                record['preconditions'].extend(['authentic_builtin_binding:' + typename, 'authentic_stdlib_binding:math.isfinite',
                                                'json_member_guard_identity_and_body_stable:' + helper['function']])
                return record
        return record

    def analyze(self, result_facts):
        rows = []
        for result in result_facts:
            if result['callee'] not in ('json.loads', 'json.load'):
                continue
            callbacks = [self._callback(function['function'], selected['name'], function['never_returns'])
                         for selected in result['callback_results'] for function in selected['functions']]
            supported = all(r['recursive_construction_supported'] for r in callbacks)
            conditions = set(result.get('preconditions', ()))
            conditions.update(('native_json_recursive_member_construction_bound',
                               'json_reachable_decoded_members_stable_until_return'))
            for callback in callbacks:
                conditions.update(callback['preconditions'])
            row = {'contract': 'python_json_decoded_members.v1', 'node': result['node'], 'callee': result['callee'],
                   'inputs': result['inputs'], 'callback_constructors': callbacks,
                   'condition': 'successful_native_decode_and_callback_return', 'preconditions': sorted(conditions),
                   'status': 'conditional_recursive_member_construction' if supported else 'callback_member_construction_unresolved',
                   'root_types': result['output_types'], 'callback_effects_accepted': False,
                   'binding_stability_accepted': False, 'reachable_mutation_closure_accepted': False,
                   'source_audit_complete': False}
            if supported:
                row['recursive_grammar'] = {'scalars': [n for n in result['output_types'] if n not in ('dict', 'list')],
                                           'list_members': 'recursive_value',
                                           'dict_members': {'key': 'exact_str', 'value': 'recursive_value'} if 'dict' in result['output_types'] else None}
            self.graph._unknown(result['node'], 'json_recursive_member_stability_summary_required')
            for number in result['inputs']:
                self.graph._edge(number, result['node'], 'json_decoded_member_construction_control', False)
            rows.append(row)
        return rows


class PythonModuleInitialization:
    """Interpret a bounded pure module initializer in source order.

    Imported code, native exception-class construction and the import name
    remain explicit premises. Function bodies are not executed here. A
    successful record establishes initial values under those premises; it
    never establishes their stability during later calls.
    """

    def __init__(self, source_bytes):
        self.sources = source_bytes

    @staticmethod
    def _value(value):
        kind = type(value).__name__
        if type(value) is dict:
            return {'type': kind, 'items': [[key, PythonModuleInitialization._value(item)]
                                          for key, item in value.items()]}
        if type(value) in (list, tuple):
            return {'type': kind, 'items': [PythonModuleInitialization._value(item) for item in value]}
        return {'type': kind, 'value': value}

    def analyze(self, path):
        syntax = ast.parse(self.sources[path], filename=path)
        values, names, events, conditions = {}, set(), [], set()
        deferred, declarations_started, expression_count = False, False, 0
        result = {'contract': 'python_module_initialization.v1', 'path': path,
                  'source_sha256': digest(self.sources[path]), 'source_executed': False,
                  'module_initialization_accepted': False, 'binding_stability_accepted': False,
                  'global_mutation_closure_accepted': False, 'source_audit_complete': False}

        def location(node):
            return {'line': node.lineno, 'column': node.col_offset,
                    'end_line': node.end_lineno, 'end_column': node.end_col_offset}

        def fail(node, reason):
            error = ValueError('module_initialization_' + reason)
            error.initialization_source = location(node)
            raise error

        def expression(node, local=None):
            nonlocal expression_count
            expression_count += 1
            if expression_count > 8192:
                fail(node, 'expression_budget')
            local = {} if local is None else local
            if isinstance(node, ast.Constant) and type(node.value) in (str, int, bool, type(None)):
                return node.value
            if isinstance(node, ast.Name):
                if node.id in local:
                    return local[node.id]
                if node.id not in values:
                    fail(node, 'value_not_initialized:' + node.id)
                return values[node.id]
            if isinstance(node, (ast.List, ast.Tuple)):
                members = [expression(item, local) for item in node.elts]
                return tuple(members) if isinstance(node, ast.Tuple) else members
            if isinstance(node, ast.Dict):
                value = {}
                for key_node, item_node in zip(node.keys, node.values):
                    if key_node is None:
                        fail(node, 'mapping_expansion')
                    key = expression(key_node, local)
                    if type(key) is not str or key in value:
                        fail(key_node, 'dictionary_key')
                    value[key] = expression(item_node, local)
                return value
            if isinstance(node, ast.Subscript):
                receiver = expression(node.value, local)
                key = expression(node.slice, local)
                if type(receiver) is not dict or type(key) is not str or key not in receiver:
                    fail(node, 'dictionary_lookup')
                return receiver[key]
            if isinstance(node, ast.DictComp) and len(node.generators) == 1:
                generator = node.generators[0]
                call = generator.iter
                if (generator.is_async or generator.ifs or not isinstance(call, ast.Call)
                        or call.args or call.keywords or not isinstance(call.func, ast.Attribute)
                        or call.func.attr != 'items' or not isinstance(generator.target, (ast.Tuple, ast.List))
                        or len(generator.target.elts) != 2
                        or any(not isinstance(item, ast.Name) for item in generator.target.elts)):
                    fail(node, 'comprehension_shape')
                receiver = expression(call.func.value, local)
                if type(receiver) is not dict:
                    fail(call, 'comprehension_receiver')
                first, second = [item.id for item in generator.target.elts]
                if first == second:
                    fail(generator.target, 'comprehension_target')
                value = {}
                for key, item in receiver.items():
                    bound = dict(local); bound.update({first: key, second: item})
                    selected = expression(node.key, bound)
                    if type(selected) is not str or selected in value:
                        fail(node.key, 'comprehension_key')
                    value[selected] = expression(node.value, bound)
                return value
            fail(node, 'expression_unclassified:' + type(node).__name__)

        def bind(name, node):
            if name in names or name in ('__name__', '__builtins__', '__spec__', '__loader__'):
                fail(node, 'binding_replaced:' + name)
            names.add(name)

        try:
            for node in syntax.body:
                entry = {'index': len(events), 'source': location(node),
                         'ast_sha256': digest(ast.dump(node, include_attributes=False).encode())}
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and type(node.value.value) is str:
                    entry['operation'] = 'inert_string'
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if declarations_started:
                        fail(node, 'late_import_effects')
                    if isinstance(node, ast.ImportFrom) and node.module == '__future__':
                        if node.level or any(item.name != 'annotations' for item in node.names):
                            fail(node, 'future_feature')
                        deferred = True
                    elif isinstance(node, ast.ImportFrom) and (node.level or any(item.name == '*' for item in node.names)):
                        fail(node, 'import_shape')
                    imported = []
                    for item in node.names:
                        name = item.asname or (item.name.split('.')[0] if isinstance(node, ast.Import) else item.name)
                        bind(name, node); imported.append(name)
                    entry.update(operation='initial_import', bindings=imported)
                    conditions.add('initial_imports_complete_before_declarations:' + path)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    declarations_started = True
                    targets = [node.target] if isinstance(node, ast.AnnAssign) else node.targets
                    if len(targets) != 1 or not isinstance(targets[0], ast.Name) or node.value is None:
                        fail(node, 'assignment_shape')
                    if isinstance(node, ast.AnnAssign) and not deferred:
                        fail(node, 'annotation_effects')
                    value = expression(node.value)
                    name = targets[0].id; bind(name, node); values[name] = value
                    entry.update(operation='value_binding', binding=name, value=self._value(value))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    declarations_started = True
                    if node.decorator_list:
                        fail(node, 'decorator_effects')
                    arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
                                 *(item for item in (node.args.vararg, node.args.kwarg) if item is not None)]
                    if not deferred and (node.returns is not None or any(item.annotation is not None for item in arguments)):
                        fail(node, 'annotation_effects')
                    defaults = [expression(item) for item in node.args.defaults]
                    keyword_defaults = [None if item is None else self._value(expression(item)) for item in node.args.kw_defaults]
                    bind(node.name, node)
                    entry.update(operation='function_binding', binding=node.name,
                                 defaults=[self._value(item) for item in defaults], keyword_defaults=keyword_defaults,
                                 body_execution='deferred', annotation_execution='deferred' if deferred else 'absent')
                elif isinstance(node, ast.ClassDef):
                    declarations_started = True
                    if (node.decorator_list or node.keywords or len(node.bases) != 1
                            or not isinstance(node.bases[0], ast.Name)
                            or node.bases[0].id not in ('Exception', 'ValueError', 'TypeError', 'RuntimeError')
                            or node.bases[0].id in names
                            or any(not (isinstance(item, ast.Pass) or isinstance(item, ast.Expr)
                                        and isinstance(item.value, ast.Constant) and type(item.value.value) is str)
                                   for item in node.body)):
                        fail(node, 'class_creation_effects')
                    bind(node.name, node)
                    conditions.add('authentic_native_exception_base:' + node.bases[0].id)
                    entry.update(operation='native_exception_class', binding=node.name, base=node.bases[0].id)
                elif isinstance(node, ast.If):
                    expected = ast.parse("__name__ == '__main__'", mode='eval').body
                    if node.orelse or ast.dump(node.test, include_attributes=False) != ast.dump(expected, include_attributes=False):
                        fail(node, 'conditional_effects')
                    conditions.add('normal_import_name_not_main:' + path)
                    entry.update(operation='inactive_main_guard', body_execution='excluded_by_import_name')
                else:
                    fail(node, 'statement_unclassified:' + type(node).__name__)
                events.append(entry)
            result.update(status='conditional_initialized_values',
                          values={name: self._value(value) for name, value in sorted(values.items())})
        except ValueError as error:
            result.update(status='unresolved', reason=str(error),
                          failure_source=getattr(error, 'initialization_source', None))
        result.update(events=events, preconditions=sorted(conditions), expression_count=expression_count)
        return result


class PythonClosedConstructor:
    """Trace finite literal constructors without executing candidate source.

    A successful trace describes exact builtin members under explicit source
    binding and storage-stability premises. It does not establish those
    premises, module initialization, runtime execution or whole-source purity.
    """

    def __init__(self, source_bytes):
        self.sources = source_bytes
        self.modules = {}

    def _module(self, path):
        if path not in self.modules:
            syntax = ast.parse(self.sources[path], filename=path)
            bindings = {}
            deferred = any(isinstance(n, ast.ImportFrom) and n.module == '__future__' and
                           any(a.name == 'annotations' for a in n.names) for n in syntax.body)
            for node in syntax.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names = [node.name]
                elif isinstance(node, ast.Import):
                    names = [a.asname or a.name.split('.')[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [a.asname or a.name for a in node.names]
                else:
                    # Comprehension targets are conservatively included. A
                    # duplicate binding remains unresolved, never guessed.
                    names = [n.id for n in ast.walk(node) if isinstance(n, ast.Name) and
                             isinstance(n.ctx, (ast.Store, ast.Del))]
                for name in names:
                    bindings.setdefault(name, []).append(node)
            self.modules[path] = bindings, deferred
        return self.modules[path]

    def trace(self, function):
        path, identity = function.split('::', 1)
        name, coordinate = identity.rsplit('@', 1)
        bindings, deferred = self._module(path)
        rows, required, active, globals_cache = [], set(), set(), {}

        def location(node):
            return {'path': path, 'line': node.lineno, 'column': node.col_offset,
                    'end_line': node.end_lineno, 'end_column': node.end_col_offset}

        def fail(node, reason):
            error = ValueError(reason)
            error.constructor_location = location(node)
            raise error

        def emit(node, operation, value, inputs=(), **extra):
            if len(rows) >= 4096:
                fail(node, 'constructor_representation_limit')
            number = len(rows)
            rows.append({'id': number, 'source': location(node), 'operation': operation,
                         'output_type': type(value).__name__, 'inputs': list(inputs), **extra})
            return value, number

        def declaration(symbol, use):
            candidates = bindings.get(symbol, ())
            if len(candidates) != 1:
                fail(use, 'constructor_binding_missing_or_ambiguous:' + symbol)
            required.add('constructor_module_binding_stable:' + path + ':' + symbol)
            return candidates[0]

        def expression(node, local, local_names):
            if isinstance(node, ast.Constant):
                value = node.value
                if type(value) not in (str, int, bool, type(None)):
                    fail(node, 'constructor_literal_type_unresolved')
                return emit(node, 'literal', value, literal=value)
            if isinstance(node, ast.Name):
                if node.id in local:
                    value, origin = local[node.id]
                    return emit(node, 'local_read', value, [origin], name=node.id)
                if node.id in local_names:
                    fail(node, 'constructor_unbound_local:' + node.id)
                if node.id not in globals_cache:
                    declared = declaration(node.id, node)
                    token = ('global', node.id)
                    if token in active:
                        fail(node, 'constructor_recursive_global:' + node.id)
                    if not (isinstance(declared, (ast.Assign, ast.AnnAssign)) and
                            isinstance(declared.target if isinstance(declared, ast.AnnAssign) else
                                       declared.targets[0], ast.Name)):
                        fail(node, 'constructor_global_value_unresolved:' + node.id)
                    if isinstance(declared, ast.Assign) and len(declared.targets) != 1:
                        fail(declared, 'constructor_multiple_assignment_unresolved')
                    if isinstance(declared, ast.AnnAssign) and not deferred:
                        fail(declared, 'constructor_annotation_effects_unresolved')
                    if declared.value is None:
                        fail(declared, 'constructor_global_without_value')
                    active.add(token)
                    try:
                        globals_cache[node.id] = expression(declared.value, {}, set())
                    finally:
                        active.remove(token)
                value, origin = globals_cache[node.id]
                required.add('constructor_module_initial_value_matches_declaration:' + path + ':' + node.id)
                required.add('constructor_global_value_graph_stable:' + path + ':' + node.id)
                return emit(node, 'global_read', value, [origin], name=node.id)
            if isinstance(node, ast.Dict):
                value, members, inputs = {}, [], []
                for key_node, value_node in zip(node.keys, node.values):
                    if key_node is None:
                        fail(node, 'constructor_mapping_expansion_unresolved')
                    key, key_id = expression(key_node, local, local_names)
                    member, value_id = expression(value_node, local, local_names)
                    if type(key) is not str or key in value:
                        fail(key_node, 'constructor_dictionary_key_unresolved')
                    value[key] = member
                    members.append({'key': key, 'key_node': key_id, 'value_node': value_id})
                    inputs.extend((key_id, value_id))
                return emit(node, 'dictionary_construction', value, inputs, members=members)
            if isinstance(node, ast.List):
                items = [expression(n, local, local_names) for n in node.elts]
                return emit(node, 'list_construction', [v for v, _ in items], [i for _, i in items])
            if isinstance(node, ast.Subscript):
                receiver, receiver_id = expression(node.value, local, local_names)
                selector, selector_id = expression(node.slice, local, local_names)
                if type(receiver) is not dict or type(selector) is not str or selector not in receiver:
                    fail(node, 'constructor_subscript_unresolved')
                required.add('constructor_native_exact_dict_string_lookup')
                return emit(node, 'dictionary_lookup', receiver[selector], [receiver_id, selector_id], key=selector)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.keywords or any(isinstance(n, ast.Starred) for n in node.args):
                    fail(node, 'constructor_expanded_or_keyword_call_unresolved')
                if node.func.id in local_names:
                    fail(node, 'constructor_local_callable_unresolved')
                arguments = [expression(n, local, local_names) for n in node.args]
                value, returned = call(node.func.id, arguments, node)
                return emit(node, 'local_call_return', value, [*(i for _, i in arguments), returned],
                            callee=node.func.id)
            fail(node, 'constructor_expression_unresolved:' + type(node).__name__)

        def call(symbol, arguments, use):
            declared = declaration(symbol, use)
            if not isinstance(declared, ast.FunctionDef) or declared.decorator_list:
                fail(use, 'constructor_callable_unresolved:' + symbol)
            token = ('call', symbol)
            if token in active:
                fail(use, 'constructor_recursion_unresolved:' + symbol)
            signature = declared.args
            parameters = [*signature.posonlyargs, *signature.args]
            if (signature.vararg or signature.kwarg or signature.kwonlyargs or signature.defaults or
                    len(parameters) != len(arguments)):
                fail(use, 'constructor_signature_unresolved:' + symbol)
            if not deferred and (declared.returns is not None or any(p.annotation is not None for p in parameters)):
                fail(declared, 'constructor_annotation_effects_unresolved')
            required.add('constructor_callable_body_stable:' + path + ':' + symbol)
            local = {parameter.arg: value for parameter, value in zip(parameters, arguments)}
            local_names = set(local)
            for statement in declared.body:
                # Validate the whole body before interpreting a return. Even
                # unreachable binders alter Python's lexical local scope.
                if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                    local_names.add(statement.targets[0].id)
                elif isinstance(statement, ast.Return) and statement.value is not None:
                    pass
                elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and type(statement.value.value) is str:
                    pass
                else:
                    fail(statement, 'constructor_statement_unresolved:' + type(statement).__name__)
            active.add(token)
            try:
                for statement in declared.body:
                    if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and type(statement.value.value) is str:
                        continue
                    if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                        local[statement.targets[0].id] = expression(statement.value, local, local_names)
                    elif isinstance(statement, ast.Return) and statement.value is not None:
                        value, origin = expression(statement.value, local, local_names)
                        return emit(statement, 'function_return', value, [origin], function=symbol)
                    else:
                        fail(statement, 'constructor_statement_unresolved:' + type(statement).__name__)
                fail(declared, 'constructor_return_missing')
            finally:
                active.remove(token)

        result = {'contract': 'python_closed_constructor.v1', 'function': function,
                  'source_sha256': digest(self.sources[path]), 'source_executed': False,
                  'module_initialization_accepted': False,
                  'binding_stability_accepted': False, 'global_mutation_closure_accepted': False,
                  'source_audit_complete': False}
        try:
            root = bindings.get(name, ())
            if len(root) != 1 or not isinstance(root[0], ast.FunctionDef):
                raise ValueError('constructor_root_unresolved')
            if coordinate != '%d:%d' % (root[0].lineno, root[0].col_offset):
                fail(root[0], 'constructor_root_source_mismatch')
            value, origin = call(name, [], root[0])
            result.update(status='conditional_closed_builtin_tree', value=value, root=origin)
        except ValueError as error:
            result.update(status='unresolved', reason=str(error),
                          failure_source=error.constructor_location if hasattr(error, 'constructor_location') else None)
        result.update(nodes=rows, preconditions=sorted(required))
        return result


class PythonConstructorInitialization:
    """Bind a constructor trace to its module's ordered initial values.

    This substitutes initialization premises only. Borrowed storage, later
    rebinding, native operations and callable effects keep their premises.
    Both input records are rederived from source before they are combined.
    """

    def __init__(self, source_bytes):
        self.sources = source_bytes

    def bind(self, constructor, initialization):
        function = constructor['function']
        path = function.split('::', 1)[0]
        result = {'contract': 'python_constructor_initialization_binding.v1',
                  'function': function, 'source_sha256': digest(self.sources[path]),
                  'constructor_sha256': digest(stored(constructor)),
                  'initialization_sha256': None if initialization is None else digest(stored(initialization)),
                  'source_executed': False, 'module_initialization_accepted': False,
                  'binding_stability_accepted': False, 'global_mutation_closure_accepted': False,
                  'global_obligations_removed': False, 'source_audit_complete': False,
                  'global_reads': [], 'callable_bindings': [], 'substituted_preconditions': [],
                  'replacement_preconditions': [], 'remaining_preconditions': constructor['preconditions']}
        try:
            expected = PythonClosedConstructor(self.sources).trace(function)
            supplied = {name: value for name, value in constructor.items() if name != 'id'}
            require(same_json(supplied, expected), 'constructor_initialization_trace_mismatch')
            require(constructor['status'] == 'conditional_closed_builtin_tree',
                    'constructor_initialization_trace_unresolved')
            require(initialization is not None, 'constructor_initialization_record_missing')
            require(same_json(initialization, PythonModuleInitialization(self.sources).analyze(path)),
                    'constructor_initialization_record_mismatch')
            require(initialization['status'] == 'conditional_initialized_values',
                    'constructor_initialization_module_unresolved')
            events = {row['binding']: row for row in initialization['events'] if 'binding' in row}
            values, reads, callables, replaced = [], [], {}, set()
            for node in constructor['nodes']:
                require(node['id'] == len(values), 'constructor_initialization_node_order')
                operation, inputs = node['operation'], node['inputs']
                require(all(type(i) is int and 0 <= i < len(values) for i in inputs),
                        'constructor_initialization_reference_order')
                if operation == 'literal':
                    value = node['literal']
                elif operation == 'dictionary_construction':
                    value = {row['key']: values[row['value_node']] for row in node['members']}
                elif operation == 'list_construction':
                    value = [values[i] for i in inputs]
                elif operation == 'dictionary_lookup':
                    receiver, selector = [values[i] for i in inputs]
                    require(type(receiver) is dict and type(selector) is str and selector in receiver,
                            'constructor_initialization_lookup')
                    value = receiver[selector]
                elif operation in ('local_read', 'global_read', 'function_return', 'local_call_return'):
                    value = values[inputs[-1]]
                else:
                    raise ValueError('constructor_initialization_operation_unresolved:' + operation)
                require(type(value).__name__ == node['output_type'], 'constructor_initialization_value_type')
                values.append(value)
                if operation == 'global_read':
                    name = node['name']
                    encoded = PythonModuleInitialization._value(value)
                    require(name in events and events[name]['operation'] == 'value_binding',
                            'constructor_initialization_global_binding')
                    require(same_json(encoded, initialization['values'].get(name)),
                            'constructor_initialization_global_value')
                    premise = 'constructor_module_initial_value_matches_declaration:' + path + ':' + name
                    require(premise in constructor['preconditions'], 'constructor_initialization_premise_missing')
                    replaced.add(premise)
                    reads.append({'node': node['id'], 'name': name, 'value': encoded,
                                  'initializer_event': events[name]['index'],
                                  'declaration_source': events[name]['source'],
                                  'read_source': node['source'], 'substituted_precondition': premise})
                if operation == 'function_return':
                    name = node['function']
                    require(name in events and events[name]['operation'] == 'function_binding',
                            'constructor_initialization_callable_binding')
                    callables[name] = {'name': name, 'initializer_event': events[name]['index'],
                                       'source': events[name]['source'], 'ast_sha256': events[name]['ast_sha256']}
            require(same_json(values[constructor['root']], constructor['value']),
                    'constructor_initialization_result_mismatch')
            replacement = set(initialization['preconditions'])
            result.update(status='conditional_initial_values_bound', global_reads=reads,
                          callable_bindings=[callables[name] for name in sorted(callables)],
                          substituted_preconditions=sorted(replaced),
                          replacement_preconditions=sorted(replacement),
                          remaining_preconditions=sorted(set(constructor['preconditions']) - replaced | replacement))
        except (ValueError, KeyError, IndexError, TypeError) as error:
            result.update(status='unresolved', reason=str(error) if isinstance(error, ValueError)
                          else 'constructor_initialization_record_invalid')
        return result


class PythonConstructorValueStability:
    """Separate immutable contents from the binding selecting an object.

    Exact scalar contents need no mutable alias-closure proof. Their module
    binding still does. Containers retain their complete storage obligation.
    Native scalar semantics remains an explicit runtime premise.
    """

    def __init__(self, source_bytes):
        self.sources = source_bytes

    def analyze(self, constructor, initialization, binding):
        function = constructor['function']
        path = function.split('::', 1)[0]
        result = {'contract': 'python_constructor_value_stability.v1',
                  'function': function, 'source_sha256': digest(self.sources[path]),
                  'initialization_binding_sha256': digest(stored(binding)),
                  'source_executed': False, 'binding_stability_accepted': False,
                  'global_mutation_closure_accepted': False, 'global_obligations_removed': False,
                  'source_audit_complete': False, 'immutable_globals': [], 'mutable_globals': [],
                  'substituted_preconditions': [], 'replacement_preconditions': [],
                  'remaining_preconditions': binding['remaining_preconditions']}
        try:
            expected = PythonConstructorInitialization(self.sources).bind(constructor, initialization)
            require(stored(binding) == stored(expected), 'constructor_value_stability_binding_mismatch')
            require(binding['status'] == 'conditional_initial_values_bound',
                    'constructor_value_stability_initialization_unresolved')
            native = {'str': str, 'int': int, 'bool': bool, 'NoneType': type(None)}
            globals_by_name = {}
            for read in binding['global_reads']:
                globals_by_name.setdefault(read['name'], []).append(read)
            immutable, mutable, replaced = [], [], set()
            for name, reads in sorted(globals_by_name.items()):
                value = reads[0]['value']
                require(all(stored(row['value']) == stored(value) for row in reads),
                        'constructor_value_stability_read_disagreement')
                content = 'constructor_global_value_graph_stable:' + path + ':' + name
                selected = 'constructor_module_binding_stable:' + path + ':' + name
                require(content in binding['remaining_preconditions'] and selected in binding['remaining_preconditions'],
                        'constructor_value_stability_premise_missing')
                row = {'name': name, 'initial_value': value,
                       'read_nodes': [read['node'] for read in reads],
                       'initializer_event': reads[0]['initializer_event'],
                       'content_precondition': content, 'binding_precondition': selected}
                kind = value['type']
                if kind in native:
                    require(set(value) == {'type', 'value'} and type(value['value']) is native[kind],
                            'constructor_value_stability_scalar_identity')
                    immutable.append(row)
                    replaced.add(content)
                else:
                    # A container can contain mutable objects even when its
                    # outer type is immutable. Do not generalize scalar facts.
                    mutable.append(row)
            replacement = {'authentic_python_builtin_immutable_scalar_semantics'} if replaced else set()
            result.update(status='conditional_immutable_contents' if immutable else 'mutable_contents_unresolved',
                          immutable_globals=immutable, mutable_globals=mutable,
                          substituted_preconditions=sorted(replaced),
                          replacement_preconditions=sorted(replacement),
                          remaining_preconditions=sorted(set(binding['remaining_preconditions']) - replaced | replacement))
        except (ValueError, KeyError, TypeError) as error:
            result.update(status='unresolved', reason=str(error) if isinstance(error, ValueError)
                          else 'constructor_value_stability_record_invalid')
        return result


class PythonCallContextTypes(PythonSuccessfulLocalTypes):
    """Carry exact entry types through one selected source-call context.

    Different callers never share parameter facts. This is conditional body
    analysis, not execution or effect acceptance. Nested calls retain their
    own binding records for later context expansion; suspension and unknown
    entries stay explicit. No global reference or exact-type fact is removed.
    """

    def _prepare_bindings(self, bindings):
        by_scope, calls_by_scope = {}, {}
        for index, binding in enumerate(bindings):
            node = self.graph.nodes[binding['node']]
            by_scope.setdefault((node['path'], node['function']), []).append((index, binding))
        for call in self.graph.calls:
            node = self.graph.nodes[call['node']]
            calls_by_scope.setdefault((node['path'], node['function']), set()).add(call['node'])
        self.context_bindings = by_scope
        self.context_calls = calls_by_scope

    def analyze_bindings(self, bindings, conditions):
        self._prepare_bindings(bindings)
        return [self._analyze_binding(index, binding, conditions)
                for index, binding in enumerate(bindings)]

    def _analyze_binding(self, index, binding, conditions, expand_unknown=False):
        self.identity = binding['function']
        definition = self.graph.definitions[self.identity]
        self.scope = self.graph.scopes[definition['scope']]
        self.reads = {}
        required = set(binding['preconditions']) | {
            'parsed_local_callable_body:' + self.identity,
            'call_context_body_binding_stable:' + self.identity}
        state, entries = {}, []
        for formal in binding['formal_bindings']:
            values = formal['value_facts']
            if not values or any(not value.startswith('type:') for value in values):
                continue
            inputs = [argument['node'] for argument in formal['arguments']]
            guard = 'call_context_parameter_binding_stable:%s:%s' % (self.identity, formal['name'])
            entry_conditions = set(formal['preconditions']) | {guard}
            state[formal['name']] = {
                'types': frozenset(value[5:] for value in values),
                'inputs': frozenset(inputs), 'guards': frozenset(), 'assignments': frozenset(),
                'preconditions': frozenset(entry_conditions)}
            entries.append({'name': formal['name'], 'parameter_node': formal['parameter_node'],
                            'selection': formal['selection'], 'inputs': inputs,
                            'output_types': sorted(state[formal['name']]['types']),
                            'preconditions': sorted(entry_conditions)})
        status = 'conditional_body_context'
        if binding['status'] != 'conditionally_bound':
            status = 'argument_binding_unresolved'
        elif (not isinstance(self.scope['tree'], ast.FunctionDef)
              or definition['return_inventory']['suspension'] is not None):
            status = 'suspended_body_unresolved'
        elif not state:
            status = 'conditional_body_unknown_entry' if expand_unknown else 'no_exact_entry_types'
        if status in ('conditional_body_context', 'conditional_body_unknown_entry'):
            self._block(self.scope['tree'].body, state)
        reads, refinements = [], {}
        for number, names in sorted(self.reads.items()):
            for name, fact in sorted(names.items()):
                preconditions = required | set(fact['preconditions'])
                for source in fact['inputs']:
                    preconditions.update(conditions.get(source, ()))
                row = {'node': number, 'name': name, 'output_types': sorted(fact['types']),
                       'inputs': sorted(fact['inputs']),
                       'assignment_nodes': sorted(fact.get('assignments', ())),
                       'possible_guard_nodes': sorted(fact['guards']),
                       'preconditions': sorted(preconditions)}
                reads.append(row)
                refinements[number] = row
                for source in {binding['node'], binding['definition_node'], binding['activation_node'],
                               *row['inputs'], *row['assignment_nodes']}:
                    self.graph._edge(source, number, 'expanded_call_context_read_control' if expand_unknown else 'call_context_read_control', False)
        nested = []
        scope_key = self.scope['path'], self.scope['name']
        if status in ('conditional_body_context', 'conditional_body_unknown_entry'):
            for child_index, child in self.context_bindings.get(scope_key, ()):
                formals, refined = [], []
                for formal in child['formal_bindings']:
                    values = formal['value_facts']
                    needed = set(formal['preconditions']) | required
                    for argument in formal['arguments']:
                        refinement = refinements.get(argument['node'])
                        if refinement is not None:
                            needed.update(refinement['preconditions'])
                    if (child['status'] == 'conditionally_bound'
                            and formal['kind'] not in ('var_positional', 'var_keyword')
                            and len(formal['arguments']) == 1):
                        refinement = refinements.get(formal['arguments'][0]['node'])
                        if refinement is not None:
                            values = ['type:' + value for value in refinement['output_types']]
                            refined.append(formal['name'])
                    formals.append({**formal, 'value_facts': values, 'preconditions': sorted(needed)})
                child_conditions = required | set(child['preconditions'])
                for formal in formals:
                    child_conditions.update(formal['preconditions'])
                nested.append({'binding_index': child_index, 'node': child['node'],
                               'function': child['function'], 'status': child['status'],
                               'formal_bindings': formals, 'refined_formals': refined,
                               'preconditions': sorted(child_conditions),
                               'execution_proven': False, 'body_context_expanded': False})
        known_calls = {child['node'] for _, child in self.context_bindings.get(scope_key, ())}
        self.graph._unknown(binding['node'], 'call_context_body_effects_summary_required')
        return {'contract': 'python_call_context_types.v1', 'binding_index': index,
                        'node': binding['node'], 'function': self.identity,
                        'definition_node': binding['definition_node'],
                        'activation_node': binding['activation_node'], 'status': status,
                        'entry_bindings': entries, 'reads': reads, 'nested_call_bindings': nested,
                        'other_call_nodes': sorted(self.context_calls.get(scope_key, set()) - known_calls),
                        'preconditions': sorted(required), 'execution_proven': False,
                        'shared_parameter_facts_changed': False, 'body_effects_accepted': False}

    def analyze_closure(self, bindings, conditions, initial_contexts):
        """Expand actual helper bindings to a finite callsite/type-state graph.

        Equal incoming facts reuse a transfer at the same source callsite.
        Every parent edge remains, and its conditions are conjoined through
        cycles to a fixed point. This is conditional abstract analysis. It
        proves neither body effects nor runtime termination. Shared parameter
        facts and reference targets remain unchanged.
        """
        self._prepare_bindings(bindings)
        states, keys, roots, edges = [], {}, [], []
        condition_names, condition_ids = [], {}

        def intern_conditions(values):
            result = []
            for value in sorted(set(values)):
                if value not in condition_ids:
                    condition_ids[value] = len(condition_names)
                    condition_names.append(value)
                result.append(condition_ids[value])
            return sorted(result)

        def intern_state(index, formals):
            signature = tuple(tuple(sorted(formal['value_facts'])) for formal in formals)
            key = index, signature
            if key not in keys:
                number = len(states)
                keys[key] = number
                states.append({'id': number, 'binding_index': index, 'input_facts': [
                    {'name': formal['name'], 'value_facts': list(values)}
                    for formal, values in zip(bindings[index]['formal_bindings'], signature)]})
            return keys[key]

        for index, binding in enumerate(bindings):
            roots.append({'binding_index': index, 'context': intern_state(index, binding['formal_bindings'])})
        local_conditions = []
        cursor = 0
        while cursor < len(states):
            state = states[cursor]
            index = state['binding_index']
            original = bindings[index]
            formals = [{**formal, 'value_facts': incoming['value_facts']}
                       for formal, incoming in zip(original['formal_bindings'], state['input_facts'])]
            if (cursor < len(initial_contexts) and cursor == index
                    and initial_contexts[index]['status'] != 'no_exact_entry_types'):
                body = initial_contexts[index]
            else:
                body = self._analyze_binding(index, {**original, 'formal_bindings': formals},
                                             conditions, expand_unknown=True)
            required = set(body['preconditions'])
            reads = []
            for row in body['reads']:
                required.update(row['preconditions'])
                reads.append({**{key: value for key, value in row.items() if key != 'preconditions'},
                              'precondition_ids': intern_conditions(row['preconditions'])})
            for child in body['nested_call_bindings']:
                target = intern_state(child['binding_index'], child['formal_bindings'])
                edges.append({'parent_context': cursor, 'child_context': target,
                              'binding_index': child['binding_index'], 'call_node': child['node'],
                              'refined_formals': child['refined_formals'],
                              'precondition_ids': intern_conditions(child['preconditions'])})
            state.update(status=body['status'], reads=reads, other_call_nodes=body['other_call_nodes'],
                         local_precondition_ids=intern_conditions(required))
            local_conditions.append(set(state['local_precondition_ids']))
            cursor += 1

        # Bit sets intern obligations without copying long condition strings.
        # Edge conditions belong to the child; all parent obligations then
        # propagate monotonically. Recursion cannot invent a new condition.
        outgoing = [set() for state in states]
        for edge in edges:
            outgoing[edge['parent_context']].add(edge['child_context'])
            local_conditions[edge['child_context']].update(edge['precondition_ids'])
        required_bits = [sum(1 << number for number in values) for values in local_conditions]
        pending = list(range(len(states)))
        queued = set(pending)
        updates = 0
        while pending:
            parent = pending.pop()
            queued.remove(parent)
            for child in sorted(outgoing[parent]):
                combined = required_bits[child] | required_bits[parent]
                if combined != required_bits[child]:
                    required_bits[child] = combined
                    updates += 1
                    if child not in queued:
                        pending.append(child)
                        queued.add(child)
        condition_sets, set_ids = [], {}
        for state, bits in zip(states, required_bits):
            if bits not in set_ids:
                set_ids[bits] = len(condition_sets)
                values = []
                remaining = bits
                while remaining:
                    lowest = remaining & -remaining
                    values.append(lowest.bit_length() - 1)
                    remaining ^= lowest
                condition_sets.append(values)
            state['required_condition_set'] = set_ids[bits]
        return {'contract': 'python_call_context_closure.v1', 'roots': roots,
                'contexts': states, 'edges': edges, 'condition_inventory': condition_names,
                'condition_sets': condition_sets, 'condition_propagation_updates': updates,
                'context_fixed_point_reached': True, 'inherited_conditions_conjoined_for_all_facts': True,
                'entry_origin_rule': 'original root binding or retained incoming context edge',
                'execution_proven': False, 'recursion_termination_proven': False,
                'shared_parameter_facts_changed': False, 'body_effects_accepted': False}


    def dictionary_comparisons(self, closure, bindings, conditions):
        """Separate dictionary result types from member callback effects.

        Native exact-dict equality returns bool on success. Key/value
        comparisons and their truth conversion may still run arbitrary code,
        mutate reachable state or raise. Neither operand evaluation nor
        those effects are accepted by this conditional result inventory.
        """
        by_scope, call_bindings, truth_destinations = {}, {}, {}
        constructor = PythonClosedConstructor(self.graph.sources)
        constructor_ids = {}
        self.graph.closed_constructor_inventory = []
        for number, (family, operations, operands) in self.graph.operators.items():
            if family != 'Compare' or not operations or any(op not in ('Eq', 'NotEq') for op in operations):
                continue
            node = self.graph.nodes[number]
            by_scope.setdefault((node['path'], node['function']), []).append((number, operations, operands))
        for binding in bindings:
            call_bindings.setdefault(binding['node'], []).append(binding)
        for operand, destination in self.graph.truth_tests:
            truth_destinations.setdefault(operand, set()).add(destination)
        records = []
        for context in closure['contexts']:
            if context['status'] not in ('conditional_body_context', 'conditional_body_unknown_entry'):
                continue
            binding = bindings[context['binding_index']]
            path, owner = binding['function'].split('::', 1)
            owner = owner.rsplit('@', 1)[0]
            reads = {row['node']: row for row in context['reads']}
            for number, operations, operands in sorted(by_scope.get((path, owner), ())):
                selected = []
                for operand in operands:
                    read = reads.get(operand)
                    needed = set(conditions.get(operand, ()))
                    constructor_proofs = []
                    constructor_needed = set()
                    if read is not None:
                        output = read['output_types']
                        inputs = read['inputs']
                        needed.update(closure['condition_inventory'][i] for i in read['precondition_ids'])
                        origin = 'contextual_read'
                    else:
                        values = self.facts.get(operand, ())
                        output = sorted(value[5:] for value in values) if values and all(
                            value.startswith('type:') for value in values) else []
                        inputs = [operand]
                        origin = 'global_conditional_exact_fact'
                        for callee in call_bindings.get(operand, ()):
                            needed.update(callee['preconditions'])
                            needed.update(('parsed_local_callable_body:' + callee['function'],
                                           'call_context_body_binding_stable:' + callee['function']))
                            if callee['status'] == 'conditionally_bound' and not callee['formal_bindings']:
                                target = callee['function']
                                if target not in constructor_ids:
                                    proof = constructor.trace(target)
                                    proof['id'] = len(self.graph.closed_constructor_inventory)
                                    constructor_ids[target] = proof['id']
                                    self.graph.closed_constructor_inventory.append(proof)
                                constructor_proofs.append(constructor_ids[target])
                                constructor_needed.update(self.graph.closed_constructor_inventory[constructor_ids[target]]['preconditions'])
                    selected.append({'node': operand, 'output_types': output, 'inputs': inputs,
                                     'fact_origin': origin, 'preconditions': sorted(needed | constructor_needed),
                                     'non_constructor_preconditions': sorted(needed),
                                     'constructor_proofs': sorted(set(constructor_proofs))})
                if not any('dict' in row['output_types'] for row in selected):
                    continue
                exact = all(row['output_types'] == ['dict'] for row in selected)
                required = {'native_dictionary_comparison_implementation_bound'}
                for row in selected:
                    required.update(row['preconditions'])
                    self.graph._edge(row['node'], number, 'context_dictionary_operand', False)
                self.graph._edge(binding['node'], number, 'context_dictionary_call_control', False)
                self.graph._unknown(number, 'context_dictionary_member_effects_summary_required')
                records.append({'contract': 'python_context_dictionary_comparison.v1',
                                'context': context['id'], 'binding_index': context['binding_index'],
                                'function': binding['function'], 'node': number, 'operations': list(operations),
                                'operands': selected, 'required_condition_set': context['required_condition_set'],
                                'preconditions': sorted(required),
                                'status': 'conditional_successful_bool' if exact else 'operand_types_unresolved',
                                'output_types': ['bool'] if exact else [], 'condition': 'successful_return',
                                'potential_effects': ['dictionary_lookup_protocols', 'value_equality_protocols',
                                                     'member_result_truth_conversion', 'reachable_state_mutation',
                                                     'raised_exception'],
                                'truth_destinations': sorted(truth_destinations.get(number, ())),
                                'additional_result_truth_callbacks': [] if exact else None,
                                'truth_inherits_comparison_effects': True,
                                'operand_evaluation_effects_accepted': False,
                                'member_effects_accepted': False, 'global_obligations_removed': False})
        return records


class PythonConstructorComparisonDependencies:
    """Apply source-bound constructor premises to the comparisons using them.

    Premises with another origin survive. Conditional constructor facts do
    not accept comparison effects, inherited context or mutable storage.
    """

    def __init__(self, source_bytes):
        self.sources = source_bytes

    def bind(self, comparisons, constructors, initializations, bindings, stabilities):
        require(len(constructors) == len(bindings) == len(stabilities),
                'constructor_comparison_dependency_membership')
        by_path = {row['path']: row for row in initializations}
        require(len(by_path) == len(initializations), 'constructor_comparison_initialization_membership')
        initializer = PythonConstructorInitialization(self.sources)
        scalar = PythonConstructorValueStability(self.sources)
        dependencies = []
        for number, (proof, binding, stability) in enumerate(zip(constructors, bindings, stabilities)):
            require(type(proof.get('id')) is int and proof['id'] == number,
                    'constructor_comparison_constructor_identity')
            path = proof['function'].split('::', 1)[0]
            initialized = by_path.get(path)
            expected_binding = initializer.bind(proof, initialized)
            require(stored(binding) == stored(expected_binding), 'constructor_comparison_binding_mismatch')
            expected_stability = scalar.analyze(proof, initialized, binding)
            require(stored(stability) == stored(expected_stability), 'constructor_comparison_stability_mismatch')
            original = set(proof['preconditions'])
            if stability['status'] in ('conditional_immutable_contents', 'mutable_contents_unresolved'):
                remaining, status = set(stability['remaining_preconditions']), stability['status']
            elif binding['status'] == 'conditional_initial_values_bound':
                remaining, status = set(binding['remaining_preconditions']), binding['status']
            else:
                remaining, status = original, 'unresolved'
            dependencies.append({'constructor_id': number, 'function': proof['function'],
                                 'source_sha256': digest(self.sources[path]),
                                 'constructor_sha256': digest(stored(proof)),
                                 'initialization_binding_sha256': digest(stored(binding)),
                                 'value_stability_sha256': digest(stored(stability)),
                                 'status': status, 'original_preconditions': sorted(original),
                                 'substituted_preconditions': sorted(original - remaining),
                                 'replacement_preconditions': sorted(remaining - original),
                                 'remaining_preconditions': sorted(remaining)})
        result = []
        for comparison in comparisons:
            require(comparison['contract'] == 'python_context_dictionary_comparison.v1',
                    'constructor_comparison_input_contract')
            operands = []
            original_required = {'native_dictionary_comparison_implementation_bound'}
            required = set(original_required)
            for operand in comparison['operands']:
                ids = operand['constructor_proofs']
                require(all(type(i) is int and 0 <= i < len(dependencies) for i in ids)
                        and ids == sorted(set(ids)), 'constructor_comparison_operand_membership')
                base = set(operand['non_constructor_preconditions'])
                original, remaining = set(base), set(base)
                updates = [dependencies[i] for i in ids]
                for dependency in updates:
                    original.update(dependency['original_preconditions'])
                    remaining.update(dependency['remaining_preconditions'])
                require(operand['preconditions'] == sorted(original),
                        'constructor_comparison_operand_provenance')
                original_required.update(original)
                required.update(remaining)
                operands.append({**operand, 'unrefined_preconditions': operand['preconditions'],
                                 'constructor_dependency_updates': updates,
                                 'preconditions': sorted(remaining)})
            require(comparison['preconditions'] == sorted(original_required),
                    'constructor_comparison_required_provenance')
            result.append({**comparison, 'contract': 'python_context_dictionary_comparison.v2',
                           'operands': operands, 'unrefined_preconditions': comparison['preconditions'],
                           'preconditions': sorted(required)})
        return result


class PythonInputFlowGraph:
    """Conservative source graph, not a source-audit acceptance decision.

    Source is parsed, never executed. Value and control edges are distinct
    from reference propagation: hashing an object preserves its input origin
    but cannot turn the digest into a callable alias. Unmodelled operations
    and unresolved receivers/calls remain explicit obligations in the result.
    """

    def __init__(self, source_bytes):
        self.sources = {path: raw for path, raw in source_bytes.items() if path.endswith('.py')}
        self.nodes, self.edges, self.seeds = [], set(), {}
        self.scopes, self.definitions, self.modules = {}, {}, {}
        self.compiler_free_cells, self.class_cells = {}, {}
        self.compiler_scope_errors = {}
        self.class_dispatches, self.super_inputs = {}, {}
        self.symbol_lookups = set()
        self.attributes, self.calls, self.subscripts, self.iterations = [], [], [], []
        self.operators, self.truth_tests, self.slices = {}, [], {}
        self.builtin_protocol_reads, self.builtin_protocol_links = [], set()
        self.builtin_protocol_edges = []
        self.sorted_protocol_inventory = []
        self.sorted_protocol_requests = set()
        self.sequence_protocol_requests = set()
        self.hash_states, self.hash_kinds = {}, {}
        self.path_states, self.path_operations = {}, {}
        self.stream_states, self.stream_metadata, self.stream_operations = {}, {}, {}
        self.json_values, self.json_operations, self.json_callbacks = {}, {}, []
        self.json_encoding_members = set()
        self.json_protocol_links = set()
        self.dictionary_lookups, self.dictionary_writes = set(), set()
        self.dictionary_protocol_requests = set()
        self.argument_bindings = set()
        self.argument_binding_calls = {}
        self.context_inventory = []
        self.annotation_inventory, self.postponed_annotations = [], set()
        self.members, self.container_kinds, self.container_keys = {}, {}, {}
        self.container_slots, self.container_updates, self.literals = {}, {}, {}
        self.container_read_links = set()
        self.reflective_attribute_calls = {}
        self.container_constructions = {}
        self.container_transfers, self.mapping_pair_reads = set(), set()
        self.complete_containers = set()
        self.unclassified, self.controls = set(), []
        self.scope = None
        self.function = '<module>'
        for path, raw in sorted(self.sources.items()):
            require(type(raw) is bytes)
            tree = ast.parse(raw, filename=path)
            try:
                pending = [symtable.symtable(raw.decode('utf-8'), path, 'exec')]
            except SyntaxError as error:
                # Keep the source inventory for diagnostics, but never treat
                # a rejected compiler scope as an empty, accepted closure.
                self.compiler_scope_errors[path] = str(error)
                pending = []
            while pending:
                table = pending.pop()
                if table.get_type() == 'function':
                    key = (path, table.get_lineno(), table.get_name())
                    self.compiler_free_cells.setdefault(key, set()).add(tuple(sorted(table.get_frees())))
                pending.extend(table.get_children())
            # Only the legal module prefix enables PEP 563. A same-spelled
            # ordinary import or nested future statement cannot change it.
            prefix = tree.body
            if prefix and isinstance(prefix[0], ast.Expr) and isinstance(prefix[0].value, ast.Constant) and isinstance(prefix[0].value.value, str):
                prefix = prefix[1:]
            for statement in prefix:
                if not isinstance(statement, ast.ImportFrom) or statement.module != '__future__' or statement.level:
                    break
                if any(item.name == 'annotations' for item in statement.names):
                    self.postponed_annotations.add(path)
            module = Path(path).stem
            require(module not in self.modules)
            scope = self._scope(path, '<module>', 'module', None, tree)
            self.modules[module] = scope
        for scope in list(self.modules.values()):
            if scope[0] in self.compiler_scope_errors:
                self.scope = scope
                rejection = self._node('compiler_scope_rejection', self.compiler_scope_errors[scope[0]])
                self._unknown(rejection, 'native_compiler_scope_rejected')
                self.scope = None
            self._body(scope, self.scopes[scope]['tree'].body)

    def _node(self, kind, label, syntax=None):
        scope = self.scopes[self.scope] if self.scope is not None else None
        number = len(self.nodes)
        self.nodes.append({'id': number, 'path': scope['path'] if scope else '',
                           'function': self.function, 'kind': kind, 'label': label,
                           'line': getattr(syntax, 'lineno', 0),
                           'column': getattr(syntax, 'col_offset', 0)})
        return number

    def _edge(self, source, target, kind='value', identity=True):
        if source is not None and target is not None:
            self.edges.add((source, target, kind, identity))

    def _derived_node(self, kind, label, origin):
        number = self._node(kind, label)
        for field in ('path', 'function', 'line', 'column'):
            self.nodes[number][field] = self.nodes[origin][field]
        return number

    def _seed(self, node, kind, name, receiver=''):
        self.seeds.setdefault(node, set()).add((kind, name, receiver))

    def _unknown(self, node, reason):
        self.unclassified.add((node, reason))

    def _scope(self, path, name, kind, parent, tree):
        key = (path, name, getattr(tree, 'lineno', 0), getattr(tree, 'col_offset', 0))
        require(key not in self.scopes)
        local, global_names, nonlocal_names = set(), set(), set()

        class Bindings(ast.NodeVisitor):
            def visit_Name(visitor, node):
                if isinstance(node.ctx, (ast.Store, ast.Del)):
                    local.add(node.id)

            def visit_Import(visitor, node):
                local.update(item.asname or item.name.split('.')[0] for item in node.names)

            def visit_ImportFrom(visitor, node):
                local.update(item.asname or item.name for item in node.names)

            def visit_FunctionDef(visitor, node):
                local.add(node.name)

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_ClassDef(visitor, node):
                local.add(node.name)

            def visit_Lambda(visitor, node):
                pass

            def visit_Global(visitor, node):
                global_names.update(node.names)

            def visit_Nonlocal(visitor, node):
                nonlocal_names.update(node.names)

            def visit_ExceptHandler(visitor, node):
                if node.name:
                    local.add(node.name)
                visitor.generic_visit(node)

            def visit_ListComp(visitor, node):
                # Comprehension targets live in a separate scope. Assignment
                # expressions in comprehensions need a separate binding rule.
                pass

            visit_SetComp = visit_ListComp
            visit_DictComp = visit_ListComp
            visit_GeneratorExp = visit_ListComp

        bodies = tree.body if isinstance(getattr(tree, 'body', None), list) else []
        for statement in bodies:
            Bindings().visit(statement)
        arguments = getattr(tree, 'args', None)
        parameters = []
        if arguments is not None:
            parameters = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]
            parameters += [item for item in (arguments.vararg, arguments.kwarg) if item]
            local.update(item.arg for item in parameters)
        self.scopes[key] = {'path': path, 'name': name, 'kind': kind, 'parent': parent,
                            'tree': tree, 'locals': local - global_names - nonlocal_names,
                            'globals': global_names, 'nonlocals': nonlocal_names,
                            'symbols': {}, 'parameters': parameters}
        compiler_name = getattr(tree, 'name', 'lambda' if isinstance(tree, ast.Lambda) else '')
        alternatives = self.compiler_free_cells.get((path, getattr(tree, 'lineno', 0), compiler_name), ())
        self.scopes[key]['compiler_frees'] = set().union(*map(set, alternatives)) if alternatives else set()
        return key

    def _class_cell(self, scope):
        if scope not in self.class_cells:
            identity = next(key for key, value in self.definitions.items() if value['scope'] == scope)
            definition = self.definitions[identity]
            cell = self._derived_node('implicit_class_cell', '__class__', definition['node'])
            self.nodes[cell]['function'] = self.scopes[scope]['name']
            self._seed(cell, 'class', identity)
            self._edge(definition['node'], cell, 'class_cell_initialization', False)
            self._unknown(cell, 'class_creation_cell_publication_effects_required')
            self.class_cells[scope] = cell
        return self.class_cells[scope]

    def _symbol(self, name, scope=None, store=False):
        requested = self.scope if scope is None else scope
        result = self._lookup_symbol(name, scope, store)
        self.symbol_lookups.add((requested, result))
        return result

    def _lookup_symbol(self, name, scope=None, store=False):
        scope = self.scope if scope is None else scope
        record = self.scopes[scope]
        if name in record['globals']:
            while self.scopes[scope]['parent'] is not None:
                scope = self.scopes[scope]['parent']
            return self._symbol(name, scope, store=True)
        if name in record['nonlocals']:
            parent = record['parent']
            while parent is not None:
                outer = self.scopes[parent]
                if name == '__class__' and outer['kind'] == 'class' and name in record['compiler_frees']:
                    return self._class_cell(parent)
                if outer['kind'] != 'class' and name in outer['locals']:
                    return self._symbol(name, parent, store=True)
                parent = outer['parent']
            node = self._node('unresolved_name', name)
            self._unknown(node, 'nonlocal_binding_missing')
            return node
        if store or name in record['locals'] or name in record['symbols']:
            if name not in record['symbols']:
                previous = self.scope, self.function
                self.scope, self.function = scope, record['name']
                record['symbols'][name] = self._node('symbol', name)
                self.scope, self.function = previous
            return record['symbols'][name]
        parent = record['parent']
        if (name == '__class__' and name in record['compiler_frees'] and parent is not None
                and self.scopes[parent]['kind'] == 'class'):
            return self._class_cell(parent)
        while parent is not None and self.scopes[parent]['kind'] == 'class':
            parent = self.scopes[parent]['parent']
        if parent is not None:
            return self._symbol(name, parent)
        node = self._symbol(name, scope, store=True)
        # A closed builtin catalogue supplies identities, not safe API
        # summaries. Unknown names stay unknown instead of becoming builtins.
        if name in {'abs', 'all', 'any', 'ascii', 'bool', 'bytearray', 'bytes', 'callable',
                    'chr', 'compile', 'delattr', 'dict', 'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format',
                    'frozenset', 'getattr', 'hasattr', 'hash', 'hex', 'id', 'int',
                    'isinstance', 'issubclass', 'iter', 'len', 'list', 'map', 'max',
                    'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow',
                    'print', 'property', 'range', 'repr', 'reversed', 'round', 'set',
                    'setattr', 'slice', 'sorted', 'staticmethod', 'classmethod', 'str',
                    'sum', 'super', 'tuple', 'type', 'zip', 'BaseException', 'Exception',
                    'ValueError', 'TypeError', 'OSError', 'RuntimeError', 'AssertionError',
                    'KeyError', 'IndexError', 'OverflowError', 'RecursionError',
                    'UnicodeError', 'UnicodeDecodeError', 'UnicodeEncodeError',
                    'AttributeError', 'BlockingIOError', 'EOFError', 'ChildProcessError',
                    'FileExistsError', 'SyntaxError', 'TimeoutError', 'StopIteration', 'SystemExit'}:
            self._seed(node, 'external', 'builtins.' + name)
        elif name in {'__file__', '__name__', '__package__', '__doc__', '__annotations__'}:
            self._seed(node, 'external', 'interpreter.' + name)
        else:
            self._unknown(node, 'name_binding_missing')
        return node

    def _body(self, scope, statements):
        previous = self.scope, self.function, self.controls
        self.scope = scope
        self.function = self.scopes[scope]['name']
        self.controls = []
        self._sequence(statements)
        self.scope, self.function, self.controls = previous

    @staticmethod
    def _explicit_exits(syntax):
        """Inventory exits in this execution scope, including nested loops.

        Function/class bodies have their own scope. This is a conservative
        completion dependency, not a reachability or exception-effect proof.
        """
        kinds = set()
        class Exits(ast.NodeVisitor):
            def visit_FunctionDef(visitor, node):
                pass
            visit_AsyncFunctionDef = visit_FunctionDef
            visit_ClassDef = visit_FunctionDef
            visit_Lambda = visit_FunctionDef
            def visit_Return(visitor, node):
                kinds.add('return')
            def visit_Raise(visitor, node):
                kinds.add('raise')
            def visit_Assert(visitor, node):
                kinds.add('assert')
            def visit_Break(visitor, node):
                kinds.add('break')
            def visit_Continue(visitor, node):
                kinds.add('continue')
            def visit_With(visitor, node):
                # Entry/exit and exception suppression can control later
                # statements even without an explicit raise in the body.
                kinds.add('context')
                visitor.generic_visit(node)
            visit_AsyncWith = visit_With
        Exits().visit(syntax)
        return kinds

    def _sequence(self, statements):
        # A conditional exit controls the rest of its statement sequence.
        # Keep every source node for enumeration, even after an unconditional
        # exit. Completion edges never carry callable/reference identity.
        previous = list(self.controls)
        gates = []
        for statement in statements:
            before = len(self.nodes)
            self._statement(statement)
            exits = self._explicit_exits(statement)
            if exits:
                gate = self._node('statement_completion', ','.join(sorted(exits)), statement)
                for entry in self.nodes[before:gate]:
                    if entry['path'] == self.scopes[self.scope]['path'] and entry['function'] == self.function:
                        self._edge(entry['id'], gate, 'statement_completion_input', False)
                for control in self.controls:
                    self._edge(control, gate, 'statement_completion_control', False)
                self.controls.append(gate)
                gates.append(gate)
        self.controls = previous
        return gates

    def _builtin_decorator(self, syntax, scope):
        if not isinstance(syntax, ast.Name) or syntax.id not in ('property', 'staticmethod', 'classmethod'):
            return None
        symbol = self._symbol(syntax.id, scope)
        if self.seeds.get(symbol) != {('external', 'builtins.' + syntax.id, '')}:
            return None
        # A local import or assignment with this spelling is an ordinary
        # callable until its binding is separately proven. Only the actual
        # unshadowed builtin lookup may use the descriptor shortcut.
        if any(record['symbols'].get(syntax.id) == symbol and syntax.id in record['locals']
               for record in self.scopes.values()):
            return None
        return syntax.id

    def _definition(self, node):
        parent = self.scope
        outer = self.scopes[parent]
        leaf = getattr(node, 'name', '<lambda@%d:%d>' % (node.lineno, node.col_offset))
        name = leaf if outer['name'] == '<module>' else outer['name'] + '.' + leaf
        kind = 'class' if isinstance(node, ast.ClassDef) else 'function'
        scope = self._scope(outer['path'], name, kind, parent, node)
        identity = '%s::%s@%d:%d' % scope
        reference = self._node(kind + '_definition', identity, node)
        self._seed(reference, kind, identity)
        self.definitions[identity] = {'scope': scope, 'node': reference, 'kind': kind,
                                      'return': None, 'parameters': [], 'property': False,
                                      'staticmethod': False, 'classmethod': False, 'activation': None,
                                      'default_values': {},
                                      'return_sites': {}, 'return_inventory': None, 'return_values': []}
        if kind == 'class':
            self.definitions[identity]['bases'] = []
            for base in node.bases:
                value = self._expression(base)
                self.definitions[identity]['bases'].append(value)
                self._edge(value, reference, 'base', False)
                self._unknown(reference, 'class_inheritance_summary_required')
            for keyword in node.keywords:
                self._edge(self._expression(keyword.value), reference, 'class_keyword', False)
                self._unknown(reference, 'class_keyword_or_metaclass_summary_required')
            self._body(scope, node.body)
        else:
            previous = self.scope, self.function, self.controls
            self.scope, self.function, self.controls = scope, name, []
            result = self._node('return_slot', identity, node)
            activation = self._node('function_activation', identity, node)
            parameters = [self._symbol(item.arg, store=True) for item in self.scopes[scope]['parameters']]
            if '__class__' in self.scopes[scope]['compiler_frees']:
                self._symbol('__class__')
            self.definitions[identity].update({'return': result, 'parameters': parameters,
                                               'activation': activation})
            if outer['kind'] == 'class':
                class_identity = next(key for key, value in self.definitions.items() if value['scope'] == parent)
                decorators = getattr(node, 'decorator_list', [])
                builtin_decorators = {self._builtin_decorator(item, parent) for item in decorators}
                if (node.args.posonlyargs or node.args.args) and 'staticmethod' not in builtin_decorators:
                    self._seed(parameters[0], 'instance', class_identity)
                self.definitions[identity]['property'] = 'property' in builtin_decorators
                self.definitions[identity]['staticmethod'] = 'staticmethod' in builtin_decorators
                self.definitions[identity]['classmethod'] = 'classmethod' in builtin_decorators
            if isinstance(node, ast.Lambda):
                self.definitions[identity]['return_sites'][(node.lineno, node.col_offset)] = self._expression(node.body)
            else:
                self._sequence(node.body)
            self._finish_function_returns(identity, node)
            for entry in self.nodes:
                if entry['path'] == outer['path'] and entry['function'] == name and entry['kind'] in {
                        'return_slot', 'assignment_value', 'controlled_assignment', 'Call', 'exception_or_assert'}:
                    self._edge(activation, entry['id'], 'activation', False)
            self.scope, self.function, self.controls = previous
            all_args = [*node.args.posonlyargs, *node.args.args]
            defaults = list(zip(all_args[len(all_args) - len(node.args.defaults):], node.args.defaults))
            defaults += [(arg, value) for arg, value in zip(node.args.kwonlyargs, node.args.kw_defaults) if value is not None]
            for arg, default in defaults:
                value = self._expression(default)
                self.definitions[identity]['default_values'][arg.arg] = value
                self._edge(value, self._symbol(arg.arg, scope, store=True), 'default')
            annotations = [arg.annotation for arg in self.scopes[scope]['parameters'] if arg.annotation is not None]
            if getattr(node, 'returns', None) is not None:
                annotations.append(node.returns)
            for annotation in annotations:
                self._annotation(annotation, reference, 'function')
            if isinstance(node, ast.AsyncFunctionDef):
                self._unknown(reference, 'coroutine_lifecycle_summary_required')
        for decorator in reversed(getattr(node, 'decorator_list', [])):
            decorator_value = self._expression(decorator)
            builtin_decorator = self._builtin_decorator(decorator, parent)
            if builtin_decorator is not None:
                if outer['kind'] != 'class' or len(getattr(node, 'decorator_list', ())) != 1:
                    self._unknown(reference, 'descriptor_composition_summary_required')
                if builtin_decorator == 'classmethod':
                    self._unknown(reference, 'classmethod_binding_summary_required')
                continue
            wrapped = self._node('decorated_definition', identity, decorator)
            self.calls.append({'node': wrapped, 'function': decorator_value,
                               'args': [reference], 'keywords': [], 'starred': False,
                               'controls': list(self.controls)})
            reference = wrapped
        if not isinstance(node, ast.Lambda):
            self._assign(ast.Name(id=node.name, ctx=ast.Store()), reference)
        return reference

    def _annotation(self, syntax, owner, storage):
        """Separate source spelling, stored strings and executable expressions.

        Without a future import, retain the union of eager (3.9) and lazy
        (3.14) effects. No annotation is evidence of a value's runtime type.
        Local variable annotations are never evaluated on either runtime.
        """
        scope = self.scopes[self.scope]
        postponed = scope['path'] in self.postponed_annotations
        ignored = storage == 'local' or (postponed and storage == 'discarded')
        mode = 'not_evaluated' if ignored else ('stringified' if postponed else 'runtime_evaluation_required')
        value = self._node('annotation_source', ast.unparse(syntax), syntax)
        self.annotation_inventory.append({'node': value, 'owner': owner, 'storage': storage,
                                          'mode': mode, 'source': ast.unparse(syntax)})
        if ignored:
            return
        if postponed:
            self.literals[value] = ast.unparse(syntax)
            self._seed(value, 'literal', 'str')
            self._edge(value, owner, 'annotation_storage', False)
        else:
            evaluated = self._expression(syntax)
            self._edge(evaluated, value, 'annotation_evaluation', False)
            self._edge(evaluated, owner, 'annotation', False)
            self._unknown(evaluated, 'annotation_evaluation_summary_required')
        if storage in ('module', 'class'):
            # __annotations__ is writable; a replaced mapping or class
            # namespace can run callbacks when the annotation is stored.
            mapping = self._symbol('__annotations__', store=True)
            self._edge(value, mapping, 'annotation_storage', False)
            self._unknown(value, 'annotation_storage_write_summary_required')

    def _annotation_consumers(self, references):
        stored = [row['node'] for row in self.annotation_inventory
                  if row['mode'] != 'not_evaluated' and row['storage'] != 'discarded']
        consumers = set()
        for receiver, attribute, value, write in self.attributes:
            if attribute in ('__annotations__', '__annotate__'):
                consumers.add((value, 'annotation_storage_access_summary_required'))
        for node in self.nodes:
            if node['kind'] == 'name_read' and node['label'] in ('__annotations__', '__annotate__'):
                consumers.add((node['id'], 'annotation_storage_access_summary_required'))
        evaluators = {'typing.get_type_hints', 'inspect.get_annotations', 'builtins.eval', 'builtins.exec'}
        for call in self.calls:
            if any(kind == 'external' and (name in evaluators or name.startswith('annotationlib.'))
                   for kind, name, _ in references.get(call['function'], ())):
                consumers.add((call['node'], 'annotation_evaluation_summary_required'))
        for consumer, obligation in sorted(consumers):
            self._unknown(consumer, obligation)
            for source in stored:
                # Conservatively include all modules: annotations can be
                # forwarded through aliases, decorators and external code.
                self._edge(source, consumer, 'annotation_consumer_input', False)

    def _finish_function_returns(self, identity, syntax):
        definition = self.definitions[identity]
        inventory = PythonReturnFlow().analyze(syntax)
        sites = definition['return_sites']
        if inventory['supported']:
            selected = [tuple(site) for site in inventory['return_sites']]
            require(all(site in sites for site in selected), 'lcer.source_return_site_missing')
        else:
            selected = sorted(sites)
            self._unknown(definition['node'], 'function_return_flow_summary_required')
        values = [sites[site] for site in selected]
        if inventory['falls_through'] or not inventory['supported']:
            implicit = self._node('implicit_return', 'None', syntax)
            self._seed(implicit, 'literal', 'NoneType')
            self.literals[implicit] = None
            values.append(implicit)
        result = definition['return']
        if inventory['suspension']:
            # A call creates a suspended object. The body's return value is
            # eventual termination data, not that object's callable alias.
            deferred = self._node('suspended_return_slot', identity, syntax)
            self._seed(result, 'suspended_result', inventory['suspension'], identity)
            self._edge(deferred, result, 'suspended_return_provenance', False)
            self._unknown(definition['node'], inventory['suspension'] + '_lifecycle_summary_required')
            result = deferred
        for value in values:
            self._edge(value, result, 'return')
        definition['return_values'] = values
        definition['return_inventory'] = inventory

    def _assign(self, target, value):
        controlled = self._node('controlled_assignment' if self.controls else 'assignment_value', '', target)
        self._edge(value, controlled, 'assignment_value')
        for control in self.controls:
            self._edge(control, controlled, 'control', False)
        value = controlled
        if isinstance(target, ast.Name):
            destination = self._symbol(target.id, store=True)
            self._edge(value, destination, 'assignment')
            for control in self.controls:
                self._edge(control, destination, 'control', False)
        elif isinstance(target, ast.Attribute):
            receiver = self._expression(target.value)
            self.attributes.append((receiver, target.attr, value, True))
        elif isinstance(target, ast.Subscript):
            receiver, selector = self._expression(target.value), self._expression(target.slice)
            self.subscripts.append((receiver, selector, value, True))
        elif isinstance(target, (ast.Tuple, ast.List)):
            for index, item in enumerate(target.elts):
                projected = self._node('unpack', '', item)
                selector = self._node('constant_index', str(index), item)
                self.literals[selector] = index
                if any(isinstance(element, ast.Starred) for element in target.elts):
                    # Selection depends on the runtime iterable's shape. Keep
                    # an actual provenance node, not an absent-node sentinel:
                    # JSON and container inventories must retain this input.
                    selector = self._node('unpack_selector', str(index), item)
                    self._edge(value, selector, 'unpack_shape_input', False)
                    self._unknown(projected, 'starred_unpack_shape_summary_required')
                self.subscripts.append((value, selector, projected, False))
                self._assign(item, projected)
        elif isinstance(target, ast.Starred):
            self._assign(target.value, value)
        else:
            self._unknown(value, 'assignment_target_' + type(target).__name__)

    def _statement(self, node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            self._definition(node)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for item in node.names:
                module = node.module if isinstance(node, ast.ImportFrom) else item.name
                symbol = item.name if isinstance(node, ast.ImportFrom) else None
                local = item.asname or item.name.split('.')[0]
                target = self._symbol(local, store=True)
                if isinstance(node, ast.ImportFrom) and (node.level or symbol == '*'):
                    self._unknown(target, 'dynamic_import_binding')
                elif module in self.modules:
                    if symbol is None:
                        self._seed(target, 'module', module)
                    else:
                        self._edge(self._symbol(symbol, self.modules[module], store=True), target, 'import')
                else:
                    self._seed(target, 'external', module + ('.' + symbol if symbol else ''))
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            if isinstance(node, ast.AnnAssign) and node.value is None:
                event = self._node('annotation_declaration', ast.unparse(node.target), node)
                # A declaration does not assign, fetch the final attribute,
                # or call __getitem__/__setitem__. Its target components do
                # execute, including receiver and index calls.
                if isinstance(node.target, (ast.Attribute, ast.Subscript)):
                    self._edge(self._expression(node.target.value), event, 'annotation_target', False)
                if isinstance(node.target, ast.Subscript):
                    self._edge(self._expression(node.target.slice), event, 'annotation_target', False)
                storage = self.scopes[self.scope]['kind'] if node.simple else 'discarded'
                if self.scopes[self.scope]['kind'] == 'function':
                    storage = 'local'
                self._annotation(node.annotation, event, storage)
                return
            value = self._expression(node.value) if node.value is not None else self._node('uninitialized', '', node)
            if isinstance(node, ast.AugAssign):
                combined = self._node('augmented_value', type(node.op).__name__, node)
                left = self._expression(node.target)
                self._edge(left, combined, 'operator', False)
                self._edge(value, combined, 'operator', False)
                self.operators[combined] = ('AugAssign', [type(node.op).__name__], [left, value])
                self._unknown(combined, 'operand_protocol_summary_required:AugAssign')
                value = combined
            for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                self._assign(target, value)
            if isinstance(node, ast.AnnAssign):
                storage = self.scopes[self.scope]['kind'] if node.simple else 'discarded'
                if self.scopes[self.scope]['kind'] == 'function':
                    storage = 'local'
                event = self._node('annotation_declaration', ast.unparse(node.target), node)
                self._annotation(node.annotation, event, storage)
        elif isinstance(node, ast.Return):
            definition = next(value for value in self.definitions.values() if value['scope'] == self.scope)
            returned = self._expression(node.value) if node.value else self._node('constant', 'None', node)
            if node.value is None:
                self._seed(returned, 'literal', 'NoneType')
                self.literals[returned] = None
            definition['return_sites'][(node.lineno, node.col_offset)] = returned
            for control in self.controls:
                self._edge(control, definition['return'], 'control', False)
        elif isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            source = self._expression(node.iter if isinstance(node, (ast.For, ast.AsyncFor)) else node.test)
            if isinstance(node, (ast.For, ast.AsyncFor)):
                item = self._node('iteration_item', '', node)
                self.iterations.append((source, item))
                self._assign(node.target, item)
            else:
                self.truth_tests.append((source, source))
            self.controls.append(source)
            loop = None
            if isinstance(node, (ast.While, ast.For, ast.AsyncFor)) and any(self._explicit_exits(item) for item in node.body):
                loop = self._node('loop_continuation', '', node)
                self.controls.append(loop)
            gates = self._sequence(node.body)
            if loop is not None:
                for gate in gates:
                    self._edge(gate, loop, 'loop_continuation_control', False)
            self._sequence(node.orelse)
            if loop is not None:
                self.controls.pop()
            self.controls.pop()
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            self._context_statement(node)
        elif isinstance(node, ast.Try):
            gate = self._node('exception_control', '', node)
            self._unknown(gate, 'exception_control_summary_required')
            before = len(self.nodes)
            self._sequence(node.body)
            for number in range(before, len(self.nodes)):
                self._edge(number, gate, 'exception', False)
            self.controls.append(gate)
            for handler in node.handlers:
                if handler.name:
                    self._edge(gate, self._symbol(handler.name, store=True), 'exception', False)
                if handler.type:
                    self._edge(self._expression(handler.type), gate, 'exception_type', False)
                self._sequence(handler.body)
            self._sequence(node.orelse)
            self._sequence(node.finalbody)
            self.controls.pop()
        elif isinstance(node, (ast.Global, ast.Nonlocal, ast.Pass)):
            pass
        elif isinstance(node, ast.Expr):
            self._expression(node.value)
        elif isinstance(node, (ast.Raise, ast.Assert)):
            event = self._node('exception_or_assert', type(node).__name__, node)
            for child in ast.iter_child_nodes(node):
                value = self._expression(child)
                self._edge(value, event, 'exception', False)
                if isinstance(node, ast.Assert) and child is node.test:
                    self.truth_tests.append((value, event))
            for control in self.controls:
                self._edge(control, event, 'control', False)
        else:
            unresolved = self._node('unclassified_statement', type(node).__name__, node)
            self._unknown(unresolved, 'statement_semantics_' + type(node).__name__)
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.expr):
                    self._edge(self._expression(child), unresolved, 'unclassified', False)

    def _context_statement(self, syntax):
        """Trace possible context protocol paths, leaving lifecycle unproved.

        The as-target receives __enter__'s result. __exit__ receives exception
        state and controls unwinding/continuation, never that target's identity.
        Slot snapshots, exception matching, suppression and await semantics
        remain explicit obligations; source order is not runtime certification.
        """
        previous = list(self.controls)
        asynchronous = isinstance(syntax, ast.AsyncWith)
        contexts = []
        for item in syntax.items:
            receiver = self._expression(item.context_expr)
            entered = self._node('context_enter', '', item.context_expr)
            self._edge(receiver, entered, 'context_receiver', False)
            self._unknown(entered, 'context_manager_summary_required')
            result = entered
            if asynchronous:
                result = self._node('context_awaitable', '__aenter__', item.context_expr)
                self._edge(result, entered, 'context_await', False)
                self._unknown(entered, 'async_context_manager_summary_required')
            self.builtin_protocol_reads.append(({'node': result, 'controls': list(self.controls),
                                                 'result_identity': True},
                                                'context_enter', receiver,
                                                ('__aenter__' if asynchronous else '__enter__',)))
            self.controls.append(entered)
            start = len(self.nodes)
            if item.optional_vars:
                self._assign(item.optional_vars, entered)
            contexts.append({'receiver': receiver, 'enter_node': entered, 'region_start': start,
                             'asynchronous': asynchronous, 'entry_result_node': result})
        self._sequence(syntax.body)
        # Multiple managers are nested. Inner unwinding can change exception
        # state seen by the outer exit. All such dependencies are non-aliasing.
        inner_exit = None
        for context in reversed(contexts):
            origin = context['enter_node']
            end = len(self.nodes)
            arguments = [self._derived_node('context_exception_input', label, origin)
                         for label in ('type', 'value', 'traceback')]
            for argument in arguments:
                # Normal exits pass None. Exceptional exits may pass opaque
                # values; these nodes deliberately receive no complete type.
                self._seed(argument, 'literal', 'NoneType')
                for number in range(context['region_start'], end):
                    if (self.nodes[number]['path'], self.nodes[number]['function']) == (
                            self.nodes[origin]['path'], self.nodes[origin]['function']):
                        self._edge(number, argument, 'context_exception_input', False)
            exited = self._derived_node('context_exit', '', origin)
            self._unknown(exited, 'context_exception_state_summary_required')
            self._unknown(exited, 'context_slot_snapshot_summary_required')
            self._edge(origin, exited, 'context_entered_control', False)
            if inner_exit is not None:
                self._edge(inner_exit, exited, 'context_unwind_control', False)
            result = exited
            if asynchronous:
                result = self._derived_node('context_awaitable', '__aexit__', origin)
                self._edge(result, exited, 'context_await', False)
                self._unknown(exited, 'async_context_manager_summary_required')
            self.builtin_protocol_reads.append(({'node': result, 'controls': [*previous, origin],
                                                 'callback_args': arguments, 'result_identity': True},
                                                'context_exit', context['receiver'],
                                                ('__aexit__' if asynchronous else '__exit__',)))
            truth = self._derived_node('context_exit_truth', 'exception_suppression', origin)
            self._edge(exited, truth, 'context_exit_truth', False)
            self._unknown(truth, 'context_exception_suppression_summary_required')
            self.builtin_protocol_reads.append(({'node': truth, 'controls': [*previous, exited]},
                                                'context_exit_truth', exited, ('__bool__',)))
            self.truth_tests.append((exited, truth))
            context.update(exit_node=exited, exit_result_node=result, exception_nodes=arguments,
                           suppression_node=truth, inner_exit_node=inner_exit, effects_complete=False)
            self.context_inventory.append(context)
            inner_exit = truth
        self.controls = previous

    def _expression(self, node):
        if isinstance(node, ast.Name):
            result = self._node('name_read', node.id, node)
            self._edge(self._symbol(node.id), result, 'name')
            return result
        if isinstance(node, ast.Lambda):
            return self._definition(node)
        result = self._node(type(node).__name__, ast.unparse(node), node)
        if isinstance(node, ast.Constant):
            self._seed(result, 'literal', type(node.value).__name__)
            self.literals[result] = node.value
        elif isinstance(node, ast.Attribute):
            self.attributes.append((self._expression(node.value), node.attr, result, False))
        elif isinstance(node, ast.Call):
            function = self._expression(node.func)
            # Selecting a callable can select a result even when the chosen
            # class has no local __init__. Preserve that input as value/control
            # provenance, never as the returned object's callable identity.
            self._edge(function, result, 'callable_dispatch', False)
            args = [self._expression(item.value if isinstance(item, ast.Starred) else item) for item in node.args]
            keywords = [(item.arg, self._expression(item.value)) for item in node.keywords]
            call = {'node': result, 'function': function, 'args': args, 'keywords': keywords,
                    'starred': any(isinstance(item, ast.Starred) for item in node.args),
                    'controls': list(self.controls), 'lexical_scope': self.scope}
            self._call_expansions(call, node)
            self.calls.append(call)
            for control in self.controls:
                self._edge(control, result, 'control', False)
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
            if isinstance(node, (ast.Set, ast.Dict)):
                self._unknown(result, 'container_construction_protocol_summary_required:' + type(node).__name__.lower())
                self.container_constructions[result] = {'kind': type(node).__name__.lower(),
                                                       'keys': [], 'values': [], 'expanded': False}
            self._seed(result, 'container', str(result))
            self.container_kinds[str(result)] = type(node).__name__.lower()
            members = self._node('container_members', str(result), node)
            self._edge(members, result, 'contents', False)
            self.members[str(result)] = members
            if isinstance(node, ast.Dict):
                self.container_keys[str(result)] = self._node('dictionary_keys', str(result), node)
            complete = not isinstance(node, ast.Set)
            entries = list(zip(node.keys, node.values)) if isinstance(node, ast.Dict) else list(enumerate(node.elts))
            for key, child in entries:
                if isinstance(child, ast.Starred) and not isinstance(node, ast.Dict):
                    if result in self.container_constructions:
                        self.container_constructions[result]['expanded'] = True
                    iterable = self._expression(child.value)
                    item = self._node('iteration_item', 'container_expansion', child)
                    self.iterations.append((iterable, item))
                    self._edge(item, members, 'expanded_container_member')
                    complete = False
                    continue
                value = self._expression(child)
                if result in self.container_constructions:
                    self.container_constructions[result]['values'].append(value)
                known = not isinstance(node, ast.Set)
                if isinstance(node, ast.Dict):
                    if key is None:
                        self.container_constructions[result]['expanded'] = True
                        self.container_transfers.add((value, str(result), result, 'mapping'))
                        complete = False
                        continue
                    selector = self._expression(key) if key is not None else None
                    self.container_constructions[result]['keys'].append(selector)
                    self._edge(selector, members, 'dictionary_key', False)
                    self._edge(selector, self.container_keys[str(result)], 'dictionary_key_reference')
                    known = selector in self.literals
                    key = self.literals.get(selector)
                complete = complete and known
                if known:
                    slot = self._container_slot(str(result), key, result)
                    self._edge(value, slot, 'container_member')
                else:
                    self._edge(value, members, 'container_member')
                    if isinstance(node, ast.Dict):
                        self._unknown(result, 'dictionary_unpack_or_key_summary_required')
            if complete:
                self.complete_containers.add(str(result))
        elif isinstance(node, ast.Subscript):
            self.subscripts.append((self._expression(node.value), self._expression(node.slice), result, False))
        elif isinstance(node, ast.NamedExpr):
            value = self._expression(node.value)
            self._assign(node.target, value)
            self._edge(value, result, 'assignment_expression')
        elif isinstance(node, ast.IfExp):
            test = self._expression(node.test)
            self.truth_tests.append((test, result))
            self._edge(test, result, 'control', False)
            self.controls.append(test)
            self._edge(self._expression(node.body), result, 'alternative')
            self._edge(self._expression(node.orelse), result, 'alternative')
            self.controls.pop()
        elif isinstance(node, ast.BoolOp):
            previous = list(self.controls)
            for index, operand in enumerate(node.values):
                value = self._expression(operand)
                self._edge(value, result, 'short_circuit_value')
                if index + 1 < len(node.values):
                    self.truth_tests.append((value, result))
                self.controls.append(value)
            self.controls = previous
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            outer = self.scopes[self.scope]
            name = outer['name'] + '.<%s@%d:%d>' % (type(node).__name__, node.lineno, node.col_offset)
            scope = self._scope(outer['path'], name, 'comprehension', self.scope, node)
            self.scopes[scope]['locals'].update(
                item.id for generator in node.generators for item in ast.walk(generator.target)
                if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store))
            first = self._expression(node.generators[0].iter)
            previous = self.scope, self.function, self.controls
            self.scope, self.function, self.controls = scope, name, list(self.controls)
            for index, generator in enumerate(node.generators):
                source = first if index == 0 else self._expression(generator.iter)
                item = self._node('iteration_item', '', generator.target)
                self.iterations.append((source, item))
                self.controls.append(source)
                self._assign(generator.target, item)
                for condition in generator.ifs:
                    condition_value = self._expression(condition)
                    self.truth_tests.append((condition_value, result))
                    self.controls.append(condition_value)
                if generator.is_async:
                    self._unknown(result, 'async_iteration_summary_required')
            self._seed(result, 'container', str(result))
            self.container_kinds[str(result)] = {
                ast.ListComp: 'list', ast.SetComp: 'set', ast.DictComp: 'dict',
                ast.GeneratorExp: 'generator'}[type(node)]
            if isinstance(node, (ast.SetComp, ast.DictComp)):
                self._unknown(result, 'container_construction_protocol_summary_required:' + self.container_kinds[str(result)])
            members = self._node('container_members', str(result), node)
            self.members[str(result)] = members
            self._edge(members, result, 'contents', False)
            if isinstance(node, ast.DictComp):
                keys = self._node('dictionary_keys', str(result), node)
                self.container_keys[str(result)] = keys
                self._edge(self._expression(node.key), keys, 'comprehension_key')
                self._edge(keys, members, 'dictionary_key', False)
                self._edge(self._expression(node.value), members, 'comprehension_member')
            else:
                self._edge(self._expression(node.elt), members, 'comprehension_member')
            for control in self.controls:
                self._edge(control, members, 'control', False)
            if isinstance(node, ast.GeneratorExp):
                self._unknown(result, 'generator_lifecycle_summary_required')
            if any(isinstance(child, ast.NamedExpr) for child in ast.walk(node)):
                self._unknown(result, 'comprehension_assignment_expression_binding_required')
            self.scope, self.function, self.controls = previous
        elif isinstance(node, ast.Compare):
            previous = list(self.controls)
            left = self._expression(node.left)
            operands = [left]
            operations = [type(item).__name__ for item in node.ops]
            for index, comparator in enumerate(node.comparators):
                right = self._expression(comparator)
                operands.append(right)
                if index + 1 < len(node.comparators):
                    gate = self._node('comparison_step', operations[index], node)
                    self.operators[gate] = ('Compare', [operations[index]], [left, right])
                    self._unknown(gate, 'operand_protocol_summary_required:Compare')
                    self._edge(left, gate, 'comparison_operand', False)
                    self._edge(right, gate, 'comparison_operand', False)
                    for control in self.controls:
                        self._edge(control, gate, 'comparison_control', False)
                    self.truth_tests.append((gate, gate))
                    self.controls.append(gate)
                left = right
            self.controls = previous
            for value in operands:
                self._edge(value, result, 'operator', False)
            self.operators[result] = ('Compare', operations, operands)
            self._unknown(result, 'operand_protocol_summary_required:Compare')
        elif isinstance(node, (ast.BinOp, ast.UnaryOp, ast.JoinedStr,
                               ast.FormattedValue, ast.Slice, ast.Starred)):
            operands = []
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.expr):
                    value = self._expression(child)
                    operands.append(value)
                    self._edge(value, result, 'operator', False)
            if isinstance(node, (ast.BinOp, ast.UnaryOp, ast.Compare, ast.FormattedValue)):
                self._unknown(result, 'operand_protocol_summary_required:' + type(node).__name__)
            operations = [type(item).__name__ for item in node.ops] if isinstance(node, ast.Compare) else (
                [type(node.op).__name__] if isinstance(node, (ast.BinOp, ast.UnaryOp)) else [])
            if isinstance(node, ast.FormattedValue):
                operations = [str(node.conversion)]
            self.operators[result] = (type(node).__name__, operations, operands)
            if isinstance(node, ast.Slice):
                self.slices[result] = operands
        else:
            self._unknown(result, 'expression_semantics_' + type(node).__name__)
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.expr):
                    self._edge(self._expression(child), result, 'unclassified', False)
        return result

    def _references(self):
        seeds = {node: set(values) for node, values in self.seeds.items()}
        edges = {(source, target) for source, target, _, identity in self.edges if identity}
        cached = getattr(self, '_reference_cache', None)
        # Normal construction only adds facts and edges. If a caller removes
        # either, recompute instead of returning aliases from the old graph.
        if (cached is None or not cached['edges'] <= edges
                or any(not values <= seeds.get(node, set()) for node, values in cached['seeds'].items())):
            cached = {'edges': set(), 'seeds': {}, 'references': {}, 'outgoing': {}}
        references, outgoing = cached['references'], cached['outgoing']
        pending, queue = {}, deque()

        def receive(target, values):
            current = references.setdefault(target, set())
            additional = values - current
            if additional:
                current.update(additional)
                if target in pending:
                    pending[target].update(additional)
                else:
                    pending[target] = additional
                    queue.append(target)

        for source, target in edges - cached['edges']:
            outgoing.setdefault(source, set()).add(target)
            if source in references:
                receive(target, references[source])
        for node, values in seeds.items():
            receive(node, values)
        # A queued node collects deltas before its turn. Existing aliases
        # need travel only over new edges; new aliases traverse every edge.
        while queue:
            source = queue.popleft()
            values = pending.pop(source)
            for target in outgoing.get(source, ()):
                receive(target, values)
        cached.update(edges=edges, seeds=seeds)
        self._reference_cache = cached
        # Returned snapshots cannot mutate the next round's closure cache.
        return {node: set(values) for node, values in references.items()}

    def _reflective_attribute_call(self, call, identity):
        """Keep native reflective selection on the ordinary attribute graph.

        A literal selector locates storage, not a safe descriptor effect.
        Unknown names and argument expansion stay unresolved. Resolved
        builtin aliases obey the same forbidden-introspection policy as
        direct syntax. No spelling-only local callable is treated as native.
        """
        if identity not in {'builtins.getattr', 'builtins.hasattr',
                            'builtins.setattr', 'builtins.delattr'}:
            return False
        operation = identity.split('.')[-1]
        args = call['args']
        arities = {'getattr': (2, 3), 'hasattr': (2,), 'setattr': (3,), 'delattr': (2,)}
        row = {'contract': 'python_reflective_attribute_call.v1', 'node': call['node'],
               'callee_node': call['function'], 'builtin': identity, 'operation': operation,
               'argument_nodes': list(args), 'receiver_node': None, 'selector_node': None,
               'selector_literal': None, 'attribute_node': None, 'default_node': None,
               'stored_value_node': None, 'status': 'argument_shape_unresolved',
               'preconditions': ['authentic_stdlib_binding:' + identity,
                                 'native_reflective_attribute_dispatch_effects'],
               'binding_stability_accepted': False, 'effects_accepted': False,
               'source_audit_complete': False}
        self.reflective_attribute_calls[call['node'], identity] = row
        self._unknown(call['node'], 'reflective_attribute_dispatch_effects_summary_required')
        if call['starred'] or call['keywords'] or len(args) not in arities[operation]:
            self._unknown(call['node'], 'reflective_attribute_argument_shape_unresolved')
            self._seed(call['node'], 'external_result', identity)
            return True
        receiver, selector = args[:2]
        row.update(receiver_node=receiver, selector_node=selector)
        for number in (receiver, selector):
            self._edge(number, call['node'], 'reflective_attribute_input', False)
        if operation == 'getattr' and len(args) == 3:
            row['default_node'] = args[2]
            self._edge(args[2], call['node'], 'reflective_attribute_default')
        if operation == 'setattr':
            row['stored_value_node'] = args[2]
        name = self.literals.get(selector)
        if type(name) is not str:
            row['status'] = 'selector_unresolved'
            self._unknown(call['node'], 'reflective_attribute_selector_unresolved')
            self._seed(call['node'], 'external_result', identity)
            return True
        if name in PYTHON_FORBIDDEN_ATTRIBUTES | PYTHON_FORBIDDEN_NAMES:
            node = self.nodes[call['node']]
            raise SourceInputForbidden(node['path'], node['function'],
                                       operation + '.' + name, node['line'])
        row.update(selector_literal=name, status='literal_attribute_connected')
        selected = self._derived_node('reflective_attribute', operation + ':' + name, call['node'])
        row['attribute_node'] = selected
        self._edge(call['node'], selected, 'reflective_attribute_dispatch', False)
        if operation in ('getattr', 'hasattr'):
            self.attributes.append((receiver, name, selected, False))
            self._edge(selected, call['node'], 'reflective_attribute_result', operation == 'getattr')
        else:
            if operation == 'setattr':
                self._edge(args[2], selected, 'reflective_attribute_stored_value')
            else:
                # A deletion invalidates the binding. It is not a None store
                # and must not erase earlier possible values in this graph.
                self._seed(selected, 'deleted_binding', name)
                self._unknown(selected, 'reflective_attribute_deletion_effects_summary_required')
            self.attributes.append((receiver, name, selected, True))
        if operation != 'getattr':
            self._seed(call['node'], 'external_result', identity)
        return True

    def _container_slot(self, identity, key, origin):
        identity_key = identity, key
        if identity_key not in self.container_slots:
            slot = self._derived_node('container_slot', identity + '[' + repr(key) + ']', origin)
            self.container_slots[identity_key] = slot
            self._edge(slot, self.members[identity], 'container_contents')
        return self.container_slots[identity_key]

    def _container_result(self, origin, kind, suffix='result'):
        identity = '%s:%s' % (origin, suffix)
        if identity not in self.members:
            self.members[identity] = self._derived_node('container_members', identity, origin)
            self.container_kinds[identity] = kind
            if kind == 'dict':
                self.container_keys[identity] = self._derived_node('dictionary_keys', identity, origin)
        return identity

    def _container_read(self, identity, selector, value):
        # These edges are monotone. A later unknown write or a newly known
        # selector must refresh the read; unchanged transfers need no replay.
        literal = self.literals.get(selector)
        token = (identity, selector, value, selector in self.literals, literal,
                 self.container_updates.get(identity), identity in self.complete_containers)
        if token in self.container_read_links:
            return
        self.container_read_links.add(token)
        if self.container_kinds[identity] == 'dict':
            self.dictionary_lookups.add((identity, selector, value))
        storage = self.members[identity]
        if selector in self.literals:
            storage = self._container_slot(identity, self.literals[selector], value)
        self._edge(storage, value, 'item_read')
        if identity not in self.complete_containers:
            self._edge(self.members[identity], value, 'unknown_container_shape_read')
        if identity in self.container_updates:
            self._edge(self.container_updates[identity], value, 'unknown_item_read')
        self._edge(selector, value, 'subscript_selector', False)

    def _container_write(self, identity, selector, value, control):
        if self.container_kinds[identity] == 'dict':
            self.dictionary_writes.add((identity, selector, control))
        if selector in self.literals:
            storage = self._container_slot(identity, self.literals[selector], value)
        else:
            if identity not in self.container_updates:
                storage = self._derived_node('container_unknown_write', identity, value)
                self.container_updates[identity] = storage
                self._edge(storage, self.members[identity], 'unknown_item_contents')
            storage = self.container_updates[identity]
        self._edge(value, storage, 'item_write')
        self._edge(control, storage, 'mutation_control', False)
        self._edge(selector, storage, 'subscript_selector', False)
        if identity in self.container_keys:
            self._edge(selector, self.container_keys[identity], 'dictionary_key_reference')

    def _container_method(self, call, method, identity):
        """Model alias/value transfers, retaining element-protocol obligations.

        These are exact builtin containers created by syntax, not a method
        name allowlist for unknown objects. Mutations are flow-insensitive:
        deletion never erases a possible old value. Custom element equality,
        hashing, iteration and destructor effects are not silently accepted.
        """
        result, args = call['node'], call['args']
        kind = self.container_kinds[identity]
        self._edge(call['function'], result, 'container_dispatch', False)
        self._unknown(result, 'container_element_protocol_summary_required:' + kind + '.' + method)
        if call['starred'] or any(name is None for name, _ in call['keywords']):
            self._unknown(result, 'container_expanded_arguments_summary_required')
            return
        if method in ('get', 'setdefault', '__getitem__', 'pop'):
            selector = args[0] if args and kind != 'set' else None
            self._container_read(identity, selector, result)
            if len(args) > 1 and kind == 'dict':
                self._edge(args[1], result, 'missing_key_default')
                if method == 'setdefault':
                    self._container_write(identity, selector, args[1], result)
            if method in ('setdefault', 'pop'):
                self._edge(result, self.members[identity], 'mutation_control', False)
        elif method in ('append', 'add', 'insert', '__setitem__'):
            selected = args[1] if method in ('insert', '__setitem__') and len(args) >= 2 else (args[0] if args else None)
            if selected is None:
                self._unknown(result, 'container_argument_binding_mismatch')
            else:
                selector = args[0] if method == '__setitem__' else None
                self._container_write(identity, selector, selected, result)
        elif method in ('extend', 'update'):
            for argument in args:
                if kind == 'dict':
                    # update accepts mappings or iterable pairs. Keep both
                    # possibilities pending until their source identities
                    # resolve in subsequent fixed-point rounds.
                    self.container_transfers.add((argument, identity, result, 'mapping'))
                else:
                    item = self._container_result(result, 'transfer', 'iteration-input')
                    self.iterations.append((argument, self.members[item]))
                    self._container_write(identity, None, self.members[item], result)
            for name, argument in call['keywords']:
                if kind == 'dict' and name is not None:
                    selector = self._derived_node('constant_index', repr(name), result)
                    self.literals[selector] = name
                    self._container_write(identity, selector, argument, result)
                else:
                    self._unknown(result, 'container_argument_binding_mismatch')
        elif method in ('keys', 'values', 'items', 'copy'):
            output = self._container_result(result, kind if method == 'copy' else 'view')
            self._seed(result, 'container', output)
            if method == 'keys':
                self._edge(self.container_keys[identity], self.members[output], 'dictionary_keys_view')
            elif method == 'values':
                self._edge(self.members[identity], self.members[output], 'dictionary_values_view')
            elif method == 'items':
                pair = self._container_result(result, 'tuple', 'item-pair')
                self.complete_containers.add(pair)
                self._edge(self.container_keys[identity], self._container_slot(pair, 0, result), 'dictionary_item_key')
                self._edge(self.members[identity], self._container_slot(pair, 1, result), 'dictionary_item_value')
                self._seed(self.members[output], 'container', pair)
            else:
                self._edge(self.members[identity], self.members[output], 'container_copy_contents')
                if kind == 'dict':
                    self._edge(self.container_keys[identity], self.container_keys[output], 'dictionary_copy_keys')
            self._edge(self.members[output], result, 'contents', False)
        elif method in ('clear', 'reverse'):
            self._edge(result, self.members[identity], 'mutation_control', False)
        else:
            self._unknown(result, 'container_method_summary_required:' + method)

    def _call_expansions(self, call, syntax):
        """Project actual expansion values even when the callee is unresolved.

        Protocol calls remain obligations. A mapping expands through keys and
        item reads; an iterable expands through iteration. Neither object is
        itself an argument value merely because it was expanded.
        """
        positional, keywords = [], []
        origin = call['node']
        for argument, node in zip(call['args'], syntax.args):
            expanded = isinstance(node, ast.Starred)
            value = argument
            if expanded:
                value = self._derived_node('expanded_positional_value', '*argument', origin)
                self.iterations.append((argument, value))
                self._edge(value, origin, 'argument_expansion', False)
                self._unknown(origin, 'expanded_argument_binding_summary_required')
            positional.append((expanded, value))
        for name, argument in call['keywords']:
            value, key = argument, None
            if name is None:
                method = self._derived_node('expansion_keys_method', 'keys', origin)
                self.attributes.append((argument, 'keys', method, False))
                keys = self._derived_node('implicit_call', 'keyword_expansion.keys', origin)
                self.calls.append({'node': keys, 'function': method, 'args': [], 'keywords': [],
                                   'starred': False, 'controls': list(call['controls'])})
                key = self._derived_node('expanded_keyword_key', '**key', origin)
                self.iterations.append((keys, key))
                value = self._derived_node('expanded_keyword_value', '**value', origin)
                self.subscripts.append((argument, key, value, False))
                self.builtin_protocol_reads.append(({'node': value, 'controls': list(call['controls']),
                                                     'callback_args': [key], 'result_identity': True},
                                                    'keyword_expansion_item', argument, ('__getitem__',)))
                self._edge(key, origin, 'keyword_expansion_key', False)
                self._edge(value, origin, 'argument_expansion', False)
                self._unknown(origin, 'expanded_argument_binding_summary_required')
                self._unknown(origin, 'keyword_expansion_protocol_summary_required')
            keywords.append((name, value, key))
        call['positional_values'], call['keyword_values'] = positional, keywords

    def _bind(self, call, identity, bound_receiver=None, return_value=True):
        definition = self.definitions[identity]
        token = call['node'], identity, bound_receiver, return_value
        if token in self.argument_bindings:
            return
        self.argument_bindings.add(token)
        self.argument_binding_calls[token] = call
        syntax = self.scopes[definition['scope']]['tree']
        parameters = definition['parameters']
        self._edge(call['function'], definition['activation'], 'call_dispatch', False)
        for control in call['controls']:
            self._edge(control, definition['activation'], 'call_control', False)
        positional = [*syntax.args.posonlyargs, *syntax.args.args]
        args = ([(False, bound_receiver)] if bound_receiver is not None else []) + call.get(
            'positional_values', [(False, value) for value in call['args']])
        keywords = call.get('keyword_values', [(name, value, None) for name, value in call['keywords']])
        packs = {}
        for formal, kind in ((syntax.args.vararg, 'tuple'), (syntax.args.kwarg, 'dict')):
            if formal is not None:
                packed = self._container_result(call['node'], kind, 'arguments:%s:%s' % (definition['node'], formal.arg))
                packs[kind] = packed
                symbol = self._symbol(formal.arg, definition['scope'], True)
                self._seed(symbol, 'container', packed)
                self._edge(self.members[packed], symbol, 'packed_arguments', False)
                if not any(expanded for expanded, _ in args) and not any(name is None for name, _, _ in keywords):
                    self.complete_containers.add(packed)
        fixed, uncertain, minimum = set(), False, 0
        for expanded, argument in args:
            uncertain = uncertain or expanded
            if uncertain:
                self._unknown(call['node'], 'expanded_argument_binding_summary_required')
                for index in range(minimum, len(positional)):
                    self._edge(argument, parameters[index], 'expanded_argument')
                if 'tuple' in packs:
                    self._container_write(packs['tuple'], None, argument, call['node'])
                self._edge(argument, definition['activation'], 'expansion_control', False)
            else:
                if minimum < len(positional):
                    self._edge(argument, parameters[minimum], 'argument')
                    fixed.add(positional[minimum].arg)
                elif 'tuple' in packs:
                    self._edge(argument, self._container_slot(packs['tuple'], minimum - len(positional), call['node']), 'vararg')
                else:
                    self._unknown(call['node'], 'argument_binding_mismatch')
            if not expanded:
                minimum += 1
        names = {argument.arg for argument in [*syntax.args.args, *syntax.args.kwonlyargs]}
        supplied = set(fixed)
        for name, argument, selector in keywords:
            if name is None:
                self._unknown(call['node'], 'expanded_argument_binding_summary_required')
                for target in sorted(names - supplied):
                    self._edge(argument, self._symbol(target, definition['scope'], True), 'expanded_keyword_argument')
                if 'dict' in packs:
                    self._container_write(packs['dict'], selector, argument, call['node'])
                self._edge(argument, definition['activation'], 'expansion_control', False)
            elif name in names:
                if name in supplied:
                    self._unknown(call['node'], 'duplicate_argument_binding')
                else:
                    self._edge(argument, self._symbol(name, definition['scope'], True), 'keyword_argument')
                    supplied.add(name)
            elif 'dict' in packs:
                selector = self._derived_node('constant_index', repr(name), call['node'])
                self.literals[selector] = name
                self._container_write(packs['dict'], selector, argument, call['node'])
            else:
                self._unknown(call['node'], 'keyword_binding_mismatch')
        if not call['starred'] and not any(name is None for name, _, _ in keywords):
            required = {item.arg for item in positional[:len(positional) - len(syntax.args.defaults)]}
            required.update(item.arg for item, default in zip(syntax.args.kwonlyargs, syntax.args.kw_defaults) if default is None)
            if required - supplied:
                self._unknown(call['node'], 'argument_binding_mismatch')
        if return_value:
            self._edge(definition['return'], call['node'], 'call_return')

    def _argument_inventory(self, facts, conditions):
        """Keep call contexts distinct without narrowing shared parameters.

        These are conditional bindings to each possible source declaration,
        not evidence that dispatch succeeded or that its body executed.
        Definition defaults can be replaced at runtime. Expanded argument
        protocols remain unresolved, even for a conveniently shaped fixture.
        """
        records = []
        for token in sorted(self.argument_bindings,
                            key=lambda row: (row[0], row[1], -1 if row[2] is None else row[2], row[3])):
            number, identity, receiver, returns = token
            call = self.argument_binding_calls[token]
            definition = self.definitions[identity]
            syntax = self.scopes[definition['scope']]['tree'].args
            positional = [(False, receiver)] if receiver is not None else []
            positional += call.get('positional_values', [(False, value) for value in call['args']])
            keywords = call.get('keyword_values', [(name, value, None) for name, value in call['keywords']])
            formal_syntax = [(arg, 'positional_only') for arg in syntax.posonlyargs]
            formal_syntax += [(arg, 'positional_or_keyword') for arg in syntax.args]
            formal_syntax += [(arg, 'keyword_only') for arg in syntax.kwonlyargs]
            if syntax.vararg is not None:
                formal_syntax.append((syntax.vararg, 'var_positional'))
            if syntax.kwarg is not None:
                formal_syntax.append((syntax.kwarg, 'var_keyword'))
            formals = [{'name': arg.arg, 'kind': kind,
                        'parameter_node': self._symbol(arg.arg, definition['scope'], True),
                        'default_node': definition['default_values'].get(arg.arg),
                        'selection': 'unresolved', 'arguments': [], 'value_facts': [], 'preconditions': []}
                       for arg, kind in formal_syntax]
            by_name = {row['name']: row for row in formals}
            positional_names = [arg.arg for arg in [*syntax.posonlyargs, *syntax.args]]
            keyword_names = {arg.arg for arg in [*syntax.args, *syntax.kwonlyargs]}
            preconditions = {'selected_call_target:' + identity, 'authentic_callable_signature:' + identity,
                             'callable_signature_stable_during_call:' + identity}
            if receiver is not None:
                preconditions.add('bound_receiver_binding:%s:%s' % (identity, receiver))
            expanded = call['starred'] or any(flag for flag, _ in positional) or any(name is None for name, _, _ in keywords)
            errors, supplied, seen_keywords = [], set(), set()
            if not expanded:
                for index, (_, value) in enumerate(positional):
                    origin = {'node': value, 'position': index - (receiver is not None)}
                    if index < len(positional_names):
                        row = by_name[positional_names[index]]
                        row['selection'] = 'bound_receiver' if index == 0 and receiver is not None else 'positional'
                        row['arguments'].append(origin)
                        supplied.add(row['name'])
                    elif syntax.vararg is not None:
                        by_name[syntax.vararg.arg]['arguments'].append(origin)
                    else:
                        errors.append('too_many_positional_arguments')
                for name, value, _ in keywords:
                    origin = {'node': value, 'keyword': name}
                    if name in seen_keywords:
                        errors.append('duplicate_keyword:' + name)
                    seen_keywords.add(name)
                    if name in keyword_names:
                        row = by_name[name]
                        if name in supplied:
                            errors.append('multiple_values:' + name)
                        else:
                            row['selection'] = 'keyword'
                        row['arguments'].append(origin)
                        supplied.add(name)
                    elif syntax.kwarg is not None:
                        by_name[syntax.kwarg.arg]['arguments'].append(origin)
                    else:
                        errors.append(('positional_only_keyword:' if name in positional_names else 'unexpected_keyword:') + name)
                for row in formals:
                    name, kind = row['name'], row['kind']
                    if kind in ('var_positional', 'var_keyword'):
                        row['selection'] = kind
                    elif name not in supplied:
                        if row['default_node'] is None:
                            errors.append('missing_argument:' + name)
                        else:
                            row['selection'] = 'definition_default'
                            row['arguments'] = [{'node': row['default_node']}]
                            row['preconditions'] = ['authentic_default_binding:%s:%s' % (identity, name),
                                                    'default_binding_stable_during_call:%s:%s' % (identity, name)]
            status = 'expanded_binding_unresolved' if expanded else 'invalid_static_binding' if errors else 'conditionally_bound'
            for row in formals:
                inputs = [argument['node'] for argument in row['arguments']]
                required = set(row['preconditions'])
                for source in inputs:
                    required.update(conditions.get(source, ()))
                if status == 'conditionally_bound':
                    if row['kind'] == 'var_positional':
                        row['value_facts'] = ['type:tuple']
                    elif row['kind'] == 'var_keyword':
                        row['value_facts'] = ['type:dict']
                    elif len(inputs) == 1:
                        row['value_facts'] = sorted(facts.get(inputs[0], ()))
                row['preconditions'] = sorted(required)
                preconditions.update(required)
            if expanded:
                preconditions.add('expanded_argument_protocols_and_binding:' + identity)
            records.append({'contract': 'python_call_argument_binding.v1', 'node': number,
                            'callee_node': call['function'], 'function': identity,
                            'definition_node': definition['node'], 'activation_node': definition['activation'],
                            'bound_receiver_node': receiver, 'returns_to_call': returns,
                            'positional_arguments': [{'expanded': flag, 'node': value} for flag, value in positional],
                            'keyword_arguments': [{'name': name, 'node': value, 'key_node': key} for name, value, key in keywords],
                            'formal_bindings': formals, 'status': status, 'errors': sorted(set(errors)),
                            'preconditions': sorted(preconditions), 'execution_proven': False,
                            'shared_parameter_facts_changed': False})
        return records

    def _builtin_callbacks(self, call, identity):
        # Derive callback edges for the exact builtin identity. This does
        # not discharge its iterable, comparison or truth-value protocols.
        if call['starred'] or any(name is None for name, _ in call['keywords']):
            return
        if identity == 'builtins.sorted':
            self._sorted_callbacks(call)
            return
        callbacks = []
        args = call['args']
        if not call['keywords']:
            protocols = {'builtins.len': ('__len__',), 'builtins.hash': ('__hash__',),
                         'builtins.bool': ('__bool__', '__len__'),
                         'builtins.chr': ('__index__',), 'builtins.hex': ('__index__',),
                         'builtins.oct': ('__index__',)}
            if identity in protocols and len(args) == 1:
                self.builtin_protocol_reads.append((call, identity, args[0], protocols[identity]))
            elif identity == 'builtins.range' and 1 <= len(args) <= 3:
                for argument in args:
                    self.builtin_protocol_reads.append((call, identity, argument, ('__index__',)))
        if identity in ('builtins.map', 'builtins.filter') and len(args) >= 2:
            callbacks.append((args[0], args[1:], 'mapped_value'))
        elif identity in ('builtins.sorted', 'builtins.min', 'builtins.max') and args:
            for name, value in call['keywords']:
                if name == 'key':
                    callbacks.append((value, args, 'ordering_key'))
        for function, iterables, purpose in callbacks:
            if function in self.literals and self.literals[function] is None:
                self._unknown(call['node'], 'builtin_element_protocol_summary_required:' + identity)
                continue
            arguments = []
            if identity in ('builtins.min', 'builtins.max') and len(iterables) > 1:
                item = self._derived_node('callback_argument', purpose, call['node'])
                for value in iterables:
                    self._edge(value, item, 'callback_argument')
                arguments.append(item)
            else:
                for source in iterables:
                    item = self._derived_node('callback_argument', purpose, call['node'])
                    self.iterations.append((source, item))
                    arguments.append(item)
            event = self._derived_node('implicit_call', identity + '.callback', call['node'])
            self.calls.append({'node': event, 'function': function, 'args': arguments,
                               'keywords': [], 'starred': False,
                               'controls': [*call['controls'], call['node']]})
            # A key controls ordering, not the identity of a selected element.
            self._edge(event, call['node'], purpose, False)
            if purpose == 'mapped_value' and identity == 'builtins.map':
                output = self._container_result(call['node'], 'generator', 'map-result')
                self._seed(call['node'], 'container', output)
                self._edge(event, self.members[output], 'map_callback_return')
            if identity != 'builtins.map':
                output_kind = 'list' if identity == 'builtins.sorted' else 'generator'
                output = self._container_result(call['node'], output_kind, 'selection-result')
                if identity in ('builtins.min', 'builtins.max'):
                    self._edge(arguments[0], call['node'], 'selected_element')
                else:
                    self._seed(call['node'], 'container', output)
                    self._edge(arguments[0], self.members[output], 'selected_element')
                self._edge(event, self.members[output], 'selection_control', False)

    def _sorted_callbacks(self, call):
        """Expose sorting's callback paths without accepting their effects.

        Key results drive comparisons; they never replace the output elements.
        Rich comparison may return an object with its own truth callback. A
        reflected comparison, tuple/list element comparison, reverse conversion
        and iterable length hint must not disappear behind the native call.
        These are possible paths, not a claim about callback order or frequency.
        """
        names = [name for name, _ in call['keywords']]
        if len(call['args']) != 1 or len(names) != len(set(names)) or any(
                name not in ('key', 'reverse') for name in names):
            self._unknown(call['node'], 'sorted_argument_binding_summary_required')
            return
        keywords = dict(call['keywords'])
        key = keywords.get('key')
        keyed = key is not None and not (key in self.literals and self.literals[key] is None)
        iterable = call['args'][0]
        element = self._derived_node('callback_argument', 'ordering_key' if keyed else 'ordering_element', call['node'])
        self.iterations.append((iterable, element))
        callback = None
        if keyed:
            callback = self._derived_node('implicit_call', 'builtins.sorted.callback', call['node'])
            self.calls.append({'node': callback, 'function': key, 'args': [element],
                               'keywords': [], 'starred': False,
                               'controls': [*call['controls'], call['node']]})
            self._edge(callback, call['node'], 'ordering_key', False)
        else:
            self._unknown(call['node'], 'builtin_element_protocol_summary_required:builtins.sorted')
        output = self._container_result(call['node'], 'list', 'selection-result')
        self._seed(call['node'], 'container', output)
        self._edge(element, self.members[output], 'selected_element')
        if callback is not None:
            self._edge(callback, self.members[output], 'selection_control', False)
        operand = callback if keyed else element
        comparison = self._derived_node('ordering_comparison', 'Lt', call['node'])
        self.operators[comparison] = ('Compare', ['Lt'], [operand, operand])
        self._edge(operand, comparison, 'ordering_operand', False)
        self._edge(comparison, call['node'], 'ordering_comparison', False)
        self._unknown(comparison, 'operand_protocol_summary_required:Compare')
        reverse = keywords.get('reverse')
        reverse_conversion = None
        if reverse is not None:
            reverse_conversion = self._derived_node('ordering_reverse_conversion', 'reverse', call['node'])
            self._edge(reverse_conversion, call['node'], 'ordering_reverse', False)
            self.truth_tests.append((reverse, reverse_conversion))
            # The supported native runtimes differ: 3.9 uses an integer
            # conversion, while 3.14 uses truth conversion. Keep both possible
            # paths until the executed runtime's converter is bound.
            self.builtin_protocol_reads.append(({'node': reverse_conversion, 'controls': [call['node']]},
                                                'sorted_truth', reverse, ('__bool__', '__len__')))
            self.builtin_protocol_reads.append(({'node': reverse_conversion, 'controls': [call['node']]},
                                                'sorted_reverse_index', reverse, ('__index__',)))
        self.builtin_protocol_reads.append(({'node': element, 'controls': [call['node']]},
                                            'sorted_length_hint', iterable, ('__len__', '__length_hint__')))
        self.sorted_protocol_inventory.append({
            'contract': 'python_sorted_protocols.v1', 'node': call['node'],
            'callee_node': call['function'], 'iterable_node': iterable,
            'element_node': element, 'key_node': key, 'key_callback_node': callback,
            'operand_node': operand, 'comparison_node': comparison,
            'reverse_node': reverse, 'reverse_conversion_node': reverse_conversion,
            'output_container': output, 'element_comparisons': [],
            'binding': 'known_static_shape',
            'preconditions': ['authentic_builtin_binding:sorted',
                              'iterable_and_length_hint_effects', 'rich_comparison_dispatch_and_effects',
                              'comparison_result_truth_effects', 'reverse_conversion_matches_runtime',
                              'temporary_release_and_finalizer_effects'],
            'native_effects_accepted': False, 'source_audit_complete': False})

    def _sorted_protocols(self, references):
        """Follow direct and lexicographic comparison slots to local bodies.

        Aggregated elements cover possible operands, not equal positions or
        an asserted comparison schedule. Recursive containers terminate by
        storage identity. Dispatch, subclasses and finalizers remain open.
        """
        def request(destination, receiver, label, methods, arguments=()):
            token = destination, receiver, label, tuple(methods), tuple(arguments)
            if token in self.sorted_protocol_requests:
                return
            self.sorted_protocol_requests.add(token)
            self.builtin_protocol_reads.append(({'node': destination, 'controls': [],
                                                 'callback_args': list(arguments),
                                                 'result_identity': label == 'sorted_compare'},
                                                label, receiver, methods))

        for row in self.sorted_protocol_inventory:
            pairs = [(row['operand_node'], row['comparison_node'], 'Lt')]
            pairs.extend((item['operand_node'], item['comparison_node'], item['operation'])
                         for item in row['element_comparisons'])
            for operand, comparison, operation in pairs:
                methods = ('__lt__', '__gt__') if operation == 'Lt' else ('__eq__',)
                request(comparison, operand, 'sorted_compare', methods, [operand])
                request(row['node'], comparison, 'sorted_truth', ('__bool__', '__len__'))
                if (comparison, row['node']) not in self.truth_tests:
                    self.truth_tests.append((comparison, row['node']))
                for kind, identity, _ in sorted(references.get(operand, ())):
                    if kind != 'container' or self.container_kinds[identity] not in ('tuple', 'list'):
                        continue
                    member = self.members[identity]
                    for element_operation in ('Eq', 'Lt'):
                        token = row['node'], identity, element_operation
                        if token in self.sorted_protocol_requests:
                            continue
                        self.sorted_protocol_requests.add(token)
                        event = self._derived_node('ordering_element_comparison', element_operation, row['node'])
                        self.operators[event] = ('Compare', [element_operation], [member, member])
                        self._edge(member, event, 'ordering_element_operand', False)
                        self._edge(event, comparison, 'ordering_lexicographic_control', False)
                        self._unknown(event, 'operand_protocol_summary_required:Compare')
                        self._unknown(comparison, 'lexicographic_comparison_dispatch_summary_required')
                        row['element_comparisons'].append({'container': identity,
                            'operand_node': member, 'comparison_node': event,
                            'parent_comparison_node': comparison, 'operation': element_operation})

    def _link_builtin_protocols(self, references):
        """Trace possible local special-method calls without accepting the API.

        Python looks these slots up on the type, bypassing instance attributes.
        Inheritance, custom descriptors and unresolved slot writes still need
        separate contracts. A traced return never becomes a builtin result's
        callable identity; len/hash/index conversion can change that value.
        """
        for outer, builtin, receiver, alternatives in self.builtin_protocol_reads:
            for kind, identity, _ in sorted(references.get(receiver, ())):
                if kind != 'instance':
                    continue
                scope = self.definitions[identity]['scope']
                symbols = self.scopes[scope]['symbols']
                # bool uses __len__ only when __bool__ is absent. A local
                # __bool__ slot takes precedence even if its value is None or
                # otherwise invalid; that fails rather than falling back.
                methods = alternatives
                if builtin in ('builtins.bool', 'dictionary_truth', 'context_exit_truth', 'sorted_truth'):
                    methods = ('__bool__',) if '__bool__' in symbols else ('__len__',)
                for method in methods:
                    symbol = symbols.get(method)
                    if symbol is None:
                        self._unknown(outer['node'], 'special_method_binding_summary_required:' + builtin + '.' + method)
                        continue
                    for member_kind, member_identity, _ in sorted(references.get(symbol, ())):
                        arguments = list(outer.get('callback_args', ()))
                        token = (outer['node'], builtin, receiver, identity, method, member_kind, member_identity,
                                 tuple(arguments))
                        if token in self.builtin_protocol_links:
                            continue
                        self.builtin_protocol_links.add(token)
                        if member_kind != 'function':
                            self._unknown(outer['node'], 'special_method_binding_summary_required:' + builtin + '.' + method)
                            continue
                        definition = self.definitions[member_identity]
                        if definition['property'] or definition['classmethod']:
                            self._unknown(outer['node'], 'special_method_descriptor_summary_required:' + builtin + '.' + method)
                            continue
                        event = self._derived_node('implicit_call', builtin + '.' + method, outer['node'])
                        function = self._derived_node('special_method_reference', identity + '.' + method, outer['node'])
                        self._seed(function, 'function' if definition['staticmethod'] else 'bound',
                                   member_identity, '' if definition['staticmethod'] else identity)
                        self._edge(receiver, function, 'special_method_receiver', False)
                        self._edge(symbol, function, 'special_method_slot_dispatch', False)
                        self.calls.append({'node': event, 'function': function, 'args': arguments, 'keywords': [],
                                           'starred': False, 'controls': [*outer['controls'], outer['node']]})
                        self._edge(event, outer['node'], 'builtin_protocol_result', outer.get('result_identity', False))
                        self.builtin_protocol_edges.append({'builtin_node': outer['node'], 'builtin': builtin,
                                                           'receiver': receiver, 'class': identity,
                                                           'method': method, 'callback_node': event,
                                                           'binding': 'possible_local_slot',
                                                           'target_definition': member_identity,
                                                           'argument_nodes': arguments})

    def _sequence_protocols(self, references):
        """Trace possible slot calls; this does not discharge their effects."""
        def request(destination, receiver, label, method, result_identity=False):
            if receiver is None:
                return
            token = destination, receiver, label, method
            if token in self.sequence_protocol_requests:
                return
            self.sequence_protocol_requests.add(token)
            self.builtin_protocol_reads.append(({'node': destination, 'controls': [],
                                                 'result_identity': result_identity},
                                                label, receiver, (method,)))

        def index(destination, selector):
            if selector in self.slices:
                for bound in self.slices[selector]:
                    request(destination, bound, 'sequence_index', '__index__')
            else:
                request(destination, selector, 'sequence_index', '__index__')

        for receiver, selector, result, _ in self.subscripts:
            if any((kind == 'container' and self.container_kinds[identity] in ('list', 'tuple'))
                   or (kind == 'literal' and identity in ('str', 'bytes'))
                   or (kind == 'external_result' and identity == 'builtins.range')
                   for kind, identity, _ in references.get(receiver, ())):
                index(result, selector)
        for call in self.calls:
            for kind, method, receiver in sorted(references.get(call['function'], ())):
                if kind == 'container_method' and self.container_kinds[receiver] == 'list' and method in (
                        'insert', 'pop', '__getitem__', '__setitem__') and call['args'] and not call['starred']:
                    index(call['node'], call['args'][0])
        for receiver, result in self.iterations:
            request(result, receiver, 'iteration', '__iter__')
        # __iter__ returns the iterator. __next__ returns the actual item,
        # including a possible callable identity. Index conversion does not.
        for edge in self.builtin_protocol_edges:
            if edge['builtin'] == 'iteration' and edge['method'] == '__iter__':
                request(edge['builtin_node'], edge['callback_node'], 'iteration_next', '__next__', True)

    def _dictionary_protocols(self):
        """Trace possible key callbacks without accepting a dictionary effect.

        Key hashing, stored-key equality, reflected equality and conversion of
        an equality result to truth can all execute local code. Collision and
        subtype ordering are not inferred here; every possible callback stays
        an obligation until its input and dispatch contracts are proved.
        """
        def request(destination, receiver, label, method, arguments=()):
            if receiver is None:
                return
            token = destination, receiver, label, method, tuple(arguments)
            if token in self.dictionary_protocol_requests:
                return
            self.dictionary_protocol_requests.add(token)
            self.builtin_protocol_reads.append(({'node': destination, 'controls': [],
                                                 'callback_args': list(arguments)},
                                                label, receiver, (method,)))

        actions = set(self.dictionary_lookups) | set(self.dictionary_writes)
        for number, construction in self.container_constructions.items():
            if construction['kind'] == 'dict':
                actions.update((str(number), selector, number) for selector in construction['keys'])
        for identity, selector, destination in sorted(actions, key=lambda row: (row[0], -1 if row[1] is None else row[1], row[2])):
            if selector is None:
                continue
            keys = self.container_keys[identity]
            request(destination, selector, 'dictionary_hash', '__hash__')
            request(destination, keys, 'dictionary_equal', '__eq__', (selector,))
            request(destination, selector, 'dictionary_reflected_equal', '__eq__', (keys,))
        for edge in self.builtin_protocol_edges:
            if edge['builtin'] in ('dictionary_equal', 'dictionary_reflected_equal'):
                # Equality may return an arbitrary object. Truth conversion
                # does not make that object the dictionary's selected value.
                request(edge['builtin_node'], edge['callback_node'], 'dictionary_truth', '__bool__')

    def _builtin_container(self, call, identity):
        kinds = {'builtins.list': 'list', 'builtins.tuple': 'tuple', 'builtins.dict': 'dict',
                 'builtins.set': 'set', 'builtins.frozenset': 'frozenset'}
        if identity not in kinds:
            return False
        kind, result = kinds[identity], call['node']
        output = self._container_result(result, kind, 'builtin-container')
        self._seed(result, 'container', output)
        if call['starred'] or any(name is None for name, _ in call['keywords']):
            self._unknown(result, 'container_expanded_arguments_summary_required')
        elif len(call['args']) > 1 or (kind != 'dict' and call['keywords']):
            self._unknown(result, 'container_argument_binding_mismatch')
        else:
            for argument in call['args']:
                if kind == 'dict':
                    self.container_transfers.add((argument, output, result, 'mapping'))
                else:
                    self.iterations.append((argument, self.members[output]))
            for name, argument in call['keywords']:
                selector = self._derived_node('constant_index', repr(name), result)
                self.literals[selector] = name
                self._container_write(output, selector, argument, result)
            if not call['args']:
                self.complete_containers.add(output)
        self._edge(self.members[output], result, 'contents', False)
        return True

    def _hash_object(self, origin, algorithm):
        identity = '%s:%s' % (origin, algorithm)
        if identity not in self.hash_states:
            self.hash_states[identity] = self._derived_node('hash_state', identity, origin)
            self.hash_kinds[identity] = algorithm
        self._seed(origin, 'hash_object', identity)
        return identity

    def _hash_method(self, call, method, identity):
        state = self.hash_states[identity]
        self._edge(state, call['node'], 'hash_state_read', False)
        self._edge(call['function'], call['node'], 'hash_dispatch', False)
        self._unknown(call['node'], 'hash_method_summary_required:' + method)
        inputs = [*call['args'], *(value for _, value in call['keywords'])]
        for value in inputs:
            self._edge(value, call['node'], 'hash_argument', False)
        if method == 'update':
            for value in inputs:
                self._edge(value, state, 'hash_update_input', False)
            self._edge(call['node'], state, 'hash_update_control', False)
        elif method == 'copy':
            copied = self._hash_object(call['node'], self.hash_kinds[identity])
            self._edge(state, self.hash_states[copied], 'hash_copy_state', False)
            self._edge(call['node'], self.hash_states[copied], 'hash_copy_control', False)

    def _contained_objects(self, references, slots, record=False, extra_roots=(), terminal_functions=(),
                           function_environments=None):
        """Share exact container/field reachability across escape families.

        The reference snapshot is fixed for this round. Propagate terminal
        object identities backwards through containment, including cycles.
        Integer masks are private storage for sets; no graph edge is removed.
        """
        if record and (extra_roots or terminal_functions or function_environments is not None):
            raise ValueError('lcer.containment_record_scope_mismatch')
        terminal_functions = frozenset(terminal_functions)
        families = {'module': 'module', 'hash_object': 'hash', 'path_object': 'path',
                    'path_iterator': 'path', 'path_parents': 'path',
                    'stream_object': 'stream', 'json_value': 'json'}
        instance_slots = {}
        for (owner, _), slot in slots.items():
            instance_slots.setdefault(owner, set()).add(slot)
        roots = set(extra_roots)
        for call in self.calls:
            targets = references.get(call['function'], ())
            if targets and all(kind in ('function', 'bound') for kind, _, _ in targets):
                continue
            roots.update(call['args'])
            roots.update(value for _, value in call['keywords'])
        pending, seen, parents = list(roots), set(), {}
        masks, numbers, atoms = {}, {}, []
        while pending:
            value = pending.pop()
            if value in seen:
                continue
            seen.add(value)
            bits, children = 0, set()
            for kind, identity, bound_receiver in references.get(value, ()):
                if kind in ('function', 'bound') and function_environments is not None:
                    environment = function_environments.get(identity)
                    if environment is not None:
                        # A function retains a namespace dictionary, not a
                        # module-object alias. Keep that capability typed.
                        atom = 'namespace', environment['module']
                        if atom not in numbers:
                            numbers[atom] = len(atoms)
                            atoms.append(atom)
                        bits |= 1 << numbers[atom]
                        children.update(environment['capture_nodes'])
                        children.update(environment['global_nodes'])
                if kind in ('function', 'bound') and identity in terminal_functions:
                    atom = 'function', identity
                    if atom not in numbers:
                        numbers[atom] = len(atoms)
                        atoms.append(atom)
                    bits |= 1 << numbers[atom]
                if kind in families:
                    atom = families[kind], identity
                    if atom not in numbers:
                        numbers[atom] = len(atoms)
                        atoms.append(atom)
                    bits |= 1 << numbers[atom]
                elif kind == 'container':
                    children.add(self.members[identity])
                    if identity in self.container_keys:
                        children.add(self.container_keys[identity])
                elif kind == 'instance':
                    children.update(instance_slots.get(identity, ()))
                elif kind == 'bound':
                    # A bound callable retains its receiver even when the
                    # callable is stored or passed without being invoked.
                    children.update(instance_slots.get(bound_receiver, ()))
            masks[value] = bits
            for child in children:
                parents.setdefault(child, set()).add(value)
                pending.append(child)
        queue = deque(value for value, bits in masks.items() if bits)
        deltas = {value: masks[value] for value in queue}
        while queue:
            value = queue.popleft()
            bits = deltas.pop(value)
            for parent in parents.get(value, ()):
                additional = bits & ~masks[parent]
                if additional:
                    masks[parent] |= additional
                    if parent in deltas:
                        deltas[parent] |= additional
                    else:
                        deltas[parent] = additional
                        queue.append(parent)
        decoded, empty = {0: {}}, frozenset()

        def lookup(value, family):
            bits = masks.get(value, 0)
            if bits not in decoded:
                found, remaining = {}, bits
                while remaining:
                    first = remaining & -remaining
                    label, identity = atoms[first.bit_length() - 1]
                    found.setdefault(label, set()).add(identity)
                    remaining ^= first
                decoded[bits] = {label: frozenset(values) for label, values in found.items()}
            return decoded[bits].get(family, empty)

        if record:
            # Export the raw basis separately from the reachability result.
            # A reader can replay reference propagation and storage traversal
            # without importing this analyzer or trusting a summary boolean.
            object_kinds = {'module', 'container', 'instance', 'bound'}
            argument_roots = []
            for call in self.calls:
                targets = references.get(call['function'], ())
                if targets and all(kind in ('function', 'bound') for kind, _, _ in targets):
                    continue
                argument_roots.append({
                    'call_node': call['node'], 'callee_node': call['function'],
                    'targets': [list(value) for value in sorted(targets)],
                    'positional': list(call['args']),
                    'keywords': [{'name': name, 'node': number} for name, number in call['keywords']]})
            lookup.inventory = {
                'contract': 'python_object_containment_graph.v2',
                'scope': 'arguments_of_nonlocal_or_unresolved_calls',
                'reference_seeds': [
                    {'node': number, 'kind': kind, 'identity': identity,
                     **({'receiver': receiver} if kind == 'bound' else {})}
                    for number, values in sorted(self.seeds.items())
                    for kind, identity, receiver in sorted(values) if kind in object_kinds],
                'containers': [
                    {'identity': identity, 'kind': self.container_kinds[identity],
                     'members_node': members, 'keys_node': self.container_keys.get(identity)}
                    for identity, members in sorted(self.members.items())],
                'instance_fields': [
                    {'owner': owner, 'attribute': attribute, 'node': number,
                     'definition_node': self.definitions[owner]['node']}
                    for (owner, attribute), number in sorted(slots.items())],
                'argument_roots': argument_roots,
                'roots': sorted(roots),
                'nodes': [
                    {'node': number,
                     'objects': [{'kind': kind, 'identity': identity,
                                  **({'receiver': receiver} if kind == 'bound' else {})}
                                 for kind, identity, receiver in sorted(references.get(number, ()))
                                 if kind in object_kinds]}
                    for number in sorted(seen)],
                'storage_edges': [
                    {'source': parent, 'target': child}
                    for child, owners in sorted(parents.items()) for parent in sorted(owners)],
                'root_modules': [{'node': number, 'modules': sorted(lookup(number, 'module'))}
                                 for number in sorted(roots)],
                'reference_seed_semantics_accepted': False,
                'bound_receiver_binding_semantics_accepted': False,
                'function_global_capture_semantics_accepted': False,
                'receiver_effects_accepted': False,
                'module_mutation_effects_accepted': False,
                'source_audit_complete': False}
        return lookup

    def _call_receiver_inventory(self, references, slots):
        """Expose attribute selection through aliases, without assuming binding.

        An attribute can invoke a descriptor or return an ordinary callable.
        The recorded receiver is the object used for that attribute lookup;
        it is not an assertion that Python passes it as a positional argument.
        """
        accesses = [{'id': index, 'receiver_node': receiver, 'attribute': attribute,
                     'value_node': value}
                    for index, (receiver, attribute, value) in enumerate(sorted({
                        (receiver, attribute, value) for receiver, attribute, value, write in self.attributes
                        if not write}))]
        outgoing, masks = {}, {}
        for source, target, _, reference in self.edges:
            if reference:
                outgoing.setdefault(source, set()).add(target)
        for access in accesses:
            number = access['value_node']
            masks[number] = masks.get(number, 0) | (1 << access['id'])
        pending = deque(masks)
        deltas = dict(masks)
        while pending:
            number = pending.popleft()
            bits = deltas.pop(number)
            for target in outgoing.get(number, ()):
                addition = bits & ~masks.get(target, 0)
                if not addition:
                    continue
                masks[target] = masks.get(target, 0) | addition
                if target in deltas:
                    deltas[target] |= addition
                else:
                    deltas[target] = addition
                    pending.append(target)
        calls, receiver_roots = [], set()
        for call in self.calls:
            bits = masks.get(call['function'], 0)
            origins = []
            while bits:
                first = bits & -bits
                origins.append(first.bit_length() - 1)
                bits ^= first
            if not origins:
                continue
            targets = sorted(references.get(call['function'], ()))
            local = bool(targets) and all(kind in ('function', 'bound') for kind, _, _ in targets)
            if not local:
                receiver_roots.update(accesses[index]['receiver_node'] for index in origins)
            calls.append({'call_node': call['node'], 'callee_node': call['function'],
                          'targets': [list(value) for value in targets], 'access_origins': origins,
                          'status': 'local_callable' if local else 'nonlocal_or_unresolved'})
        contained = self._contained_objects(references, slots, extra_roots=receiver_roots)
        modules = {number: sorted(contained(number, 'module')) for number in sorted(receiver_roots)}
        return {'contract': 'python_call_receiver_inventory.v1',
                'scope': 'attribute_reads_reaching_call_targets_through_reference_edges',
                'accesses': accesses, 'calls': calls, 'receiver_roots': sorted(receiver_roots),
                'receiver_modules': [{'node': number, 'modules': values} for number, values in modules.items()],
                'module_receivers': [
                    {'call_node': call['call_node'], 'callee_node': call['callee_node'], 'access_origin': index,
                     'receiver_node': accesses[index]['receiver_node'],
                     'modules': modules[accesses[index]['receiver_node']]}
                    for call in calls if call['status'] == 'nonlocal_or_unresolved'
                    for index in call['access_origins'] if modules[accesses[index]['receiver_node']]],
                'descriptor_binding_accepted': False, 'receiver_effects_accepted': False,
                'module_mutation_effects_accepted': False, 'source_audit_complete': False}

    def _hash_escapes(self, references, slots, contained=None):
        # Native methods and local functions have explicit state transfers.
        # Passing a hash, including one inside a container or local object's
        # fields, to other code requires a separate external mutation summary.
        if not self.hash_states:
            return
        cache = {}

        def contained_hashes(value):
            if contained is not None:
                return contained(value, 'hash')
            origin = frozenset(references.get(value, ()))
            if origin in cache:
                return cache[origin]
            pending, seen, found = [value], set(), set()
            while pending:
                item = pending.pop()
                if item in seen:
                    continue
                seen.add(item)
                values = frozenset(references.get(item, ()))
                if values in cache:
                    found.update(cache[values])
                    continue
                for kind, identity, _ in values:
                    if kind == 'hash_object':
                        found.add(identity)
                    elif kind == 'container':
                        pending.append(self.members[identity])
                        if identity in self.container_keys:
                            pending.append(self.container_keys[identity])
                    elif kind == 'instance':
                        pending.extend(slot for (owner, _), slot in slots.items() if owner == identity)
            cache[origin] = found
            return found

        for call in self.calls:
            targets = references.get(call['function'], ())
            if targets and all(kind in ('function', 'bound', 'hash_method') for kind, _, _ in targets):
                continue
            arguments = [*call['args'], *(value for _, value in call['keywords'])]
            for identity in set().union(*(contained_hashes(value) for value in arguments)):
                state = self.hash_states[identity]
                for argument in arguments:
                    self._edge(argument, call['node'], 'hash_external_argument', False)
                self._edge(state, call['node'], 'hash_external_read', False)
                self._edge(call['node'], state, 'hash_external_mutation', False)
                self._unknown(call['node'], 'hash_external_mutation_summary_required')

    def _path_operation(self, node, api, inputs, result_kind, effects=()):
        """Expose a possible pathlib branch without closing its effects.

        These are conditional receiver contracts, not complete type facts.
        Path subclasses, rebinding, argument protocols, platform behavior and
        unsuccessful calls remain obligations. Even a known path result keeps
        an external-result alternative; it must never discharge primitive
        operations merely because a may-alias set contains a Path.
        """
        key = node, api
        if key not in self.path_operations:
            row = {'node': node, 'api': api, 'inputs': set(), 'result_kind': result_kind,
                   'effects': {}, 'preconditions': ['authentic_stdlib_binding:pathlib',
                       'receiver_and_operand_dispatch_classified',
                       'argument_protocols_and_effects_classified', 'successful_declared_api_call'],
                   'classification': 'conditional_possible_branch'}
            self.path_operations[key] = row
            for effect in effects:
                endpoint = self._derived_node('path_' + effect, api, node)
                row['effects'][effect] = endpoint
                if effect == 'filesystem_write':
                    self._edge(node, endpoint, 'path_filesystem_write', False)
                else:
                    self._edge(endpoint, node, 'path_' + effect, False)
        row = self.path_operations[key]
        require(row['result_kind'] == result_kind)
        for value in inputs:
            row['inputs'].add(value)
            self._edge(value, node, 'path_input', False)
        self._unknown(node, 'stdlib_binding_summary_required:pathlib')
        self._unknown(node, 'path_api_effects_summary_required:' + api)
        self._seed(node, 'external_result', api)
        if result_kind in ('path_object', 'path_parents', 'path_iterator'):
            identity = '%s:%s' % (node, result_kind)
            if identity not in self.path_states:
                self.path_states[identity] = self._derived_node('path_state', identity, node)
            self._seed(node, result_kind, identity)
            self._edge(node, self.path_states[identity], 'path_state_input', False)

    def _path_attribute(self, receiver, identity, attribute, value, write):
        state = self.path_states[identity]
        self._edge(state, value, 'path_attribute_input', False)
        self._edge(receiver, value, 'path_receiver', False)
        if write:
            self._edge(value, state, 'path_attribute_mutation', False)
            self._unknown(value, 'path_attribute_write_summary_required:' + attribute)
            return
        api = 'pathlib.Path.' + attribute
        if attribute in ('parent', 'parents'):
            self._path_operation(value, api, [receiver, state],
                                 'path_object' if attribute == 'parent' else 'path_parents')
        elif attribute in ('name', 'stem', 'suffix', 'suffixes', 'parts', 'drive', 'root', 'anchor'):
            self._path_operation(value, api, [receiver, state], 'external_result')
        elif attribute in self._path_method_contracts():
            # Retain the actual receiver expression, including alternative
            # producers. A later alias of this bound method keeps that node.
            self._seed(value, 'path_method', api, str(receiver))
            self._unknown(value, 'path_receiver_dispatch_summary_required:' + attribute)
        else:
            self._unknown(value, 'path_attribute_summary_required:' + attribute)

    @staticmethod
    def _path_method_contracts():
        # Possible successful branches shared by the supported Python runtimes.
        # No entry asserts pure behavior or a complete receiver/result type.
        result = {}
        for method in ('with_name', 'with_stem', 'with_suffix', 'joinpath', 'relative_to',
                       '__truediv__', '__rtruediv__'):
            result[method] = ('path_object', ())
        result['absolute'] = ('path_object', ('platform_input',))
        result['expanduser'] = ('path_object', ('platform_input',))
        for method in ('resolve', 'readlink'):
            result[method] = ('path_object', ('filesystem_read', 'platform_input'))
        for method in ('rename', 'replace'):
            result[method] = ('path_object', ('filesystem_write', 'platform_input'))
        for method in ('iterdir', 'glob', 'rglob'):
            result[method] = ('path_iterator', ('filesystem_read', 'platform_input'))
        for method in ('read_bytes', 'read_text', 'stat', 'lstat', 'exists', 'is_file', 'is_dir',
                       'is_symlink', 'is_mount', 'is_socket', 'is_fifo', 'is_block_device',
                       'is_char_device', 'owner', 'group', 'samefile'):
            result[method] = ('external_result', ('filesystem_read', 'platform_input'))
        for method in ('write_bytes', 'write_text', 'mkdir', 'touch', 'unlink', 'rmdir',
                       'chmod', 'lchmod', 'symlink_to'):
            result[method] = ('external_result', ('filesystem_write', 'platform_input'))
        result['open'] = ('external_result', ('filesystem_read', 'filesystem_write', 'platform_input'))
        for method in ('as_posix', 'as_uri', 'is_absolute', 'is_reserved', 'is_relative_to',
                       'match', '__fspath__', '__str__'):
            result[method] = ('external_result', ())
        return result

    def _path_call(self, call, api, receiver=None):
        inputs = [call['function'], *call['args'], *(value for _, value in call['keywords'])]
        if receiver is None:
            factories = ('pathlib.Path', 'pathlib.PosixPath')
            if api in factories:
                result, effects = 'path_object', ()
            elif any(api == factory + '.' + method for factory in factories for method in ('cwd', 'home')):
                result, effects = 'path_object', ('platform_input',)
            else:
                return False
        else:
            inputs.append(receiver)
            result, effects = self._path_method_contracts()[api.rsplit('.', 1)[-1]]
            self._unknown(call['node'], 'path_receiver_dispatch_summary_required:' + api)
        self._path_operation(call['node'], api, inputs, result, effects)
        if receiver is not None and api == 'pathlib.Path.open':
            self._stream_factory(call, api)
        return True

    def _path_escapes(self, references, slots, contained=None):
        # Path internals and binding are not assumed immutable. Unknown calls
        # may mutate a passed object, including one nested in a container or
        # local field. Keep their other arguments in later path provenance.
        if not self.path_states:
            return
        cache = {}

        def contained_paths(value):
            if contained is not None:
                return contained(value, 'path')
            origin = frozenset(references.get(value, ()))
            if origin in cache:
                return cache[origin]
            pending, seen, found = [value], set(), set()
            while pending:
                item = pending.pop()
                if item in seen:
                    continue
                seen.add(item)
                values = frozenset(references.get(item, ()))
                if values in cache:
                    found.update(cache[values])
                    continue
                for kind, identity, _ in values:
                    if kind in ('path_object', 'path_iterator', 'path_parents'):
                        found.add(identity)
                    elif kind == 'container':
                        pending.append(self.members[identity])
                        if identity in self.container_keys:
                            pending.append(self.container_keys[identity])
                    elif kind == 'instance':
                        pending.extend(slot for (owner, _), slot in slots.items() if owner == identity)
            cache[origin] = found
            return found

        for call in self.calls:
            targets = references.get(call['function'], ())
            if targets and all(kind in ('function', 'bound') for kind, _, _ in targets):
                continue
            arguments = [*call['args'], *(value for _, value in call['keywords'])]
            for identity in sorted(set().union(*(contained_paths(value) for value in arguments))):
                state = self.path_states[identity]
                for argument in arguments:
                    self._edge(argument, call['node'], 'path_external_argument', False)
                self._edge(state, call['node'], 'path_external_read', False)
                self._edge(call['node'], state, 'path_external_mutation', False)
                self._unknown(call['node'], 'path_external_mutation_summary_required')

    def _stream_object(self, node, backend, factory, inputs):
        identity = '%s:%s:%s' % (node, backend, factory)
        if identity not in self.stream_states:
            self.stream_states[identity] = self._derived_node('stream_state', identity, node)
            self.stream_metadata[identity] = {'node': node, 'backend': backend, 'factory': factory}
        self._seed(node, 'stream_object', identity)
        self._seed(node, 'external_result', factory)
        state = self.stream_states[identity]
        for value in [node, *inputs]:
            self._edge(value, state, 'stream_state_input', False)
        self._unknown(node, 'stream_factory_binding_summary_required:' + factory)
        return identity

    def _stream_operation(self, node, api, identity, inputs, effects=()):
        """Record possible IO-family effects, never complete types or liveness.

        A stream may be replaced, subclassed, closed, buffered, descriptor-
        backed or wrapped around callbacks. The family-method labels below
        describe modeled protocol branches, not exact native implementations.
        """
        key = node, api, identity
        if key not in self.stream_operations:
            self.stream_operations[key] = {'node': node, 'api': api, 'stream': identity,
                'backend': self.stream_metadata[identity]['backend'], 'inputs': set(), 'effects': {},
                'preconditions': ['authentic_factory_and_io_binding', 'receiver_dispatch_classified',
                    'argument_and_callback_effects_classified', 'stream_lifecycle_classified'],
                'classification': 'conditional_possible_branch'}
            for effect in effects:
                endpoint = self._derived_node('stream_' + effect, api, node)
                self.stream_operations[key]['effects'][effect] = endpoint
                if effect in ('external_write', 'buffer_mutation'):
                    self._edge(node, endpoint, 'stream_' + effect, False)
                else:
                    self._edge(endpoint, node, 'stream_' + effect, False)
        row = self.stream_operations[key]
        for value in [self.stream_states[identity], *inputs]:
            row['inputs'].add(value)
            self._edge(value, node, 'stream_input', False)
        self._seed(node, 'external_result', api)
        self._unknown(node, 'stream_effects_summary_required:' + api)
        self._unknown(node, 'stream_lifecycle_summary_required')

    def _stream_factory(self, call, api):
        external = {'builtins.open', 'io.open', 'io.FileIO', 'os.fdopen', 'pathlib.Path.open'}
        wrappers = {'io.BufferedReader', 'io.BufferedWriter', 'io.BufferedRandom',
                    'io.BufferedRWPair', 'io.TextIOWrapper'}
        memory = {'io.BytesIO', 'io.StringIO'}
        if api not in external | wrappers | memory:
            return False
        backend = 'memory' if api in memory else ('wrapper' if api in wrappers else 'external')
        inputs = [call['function'], *call['args'], *(value for _, value in call['keywords'])]
        identity = self._stream_object(call['node'], backend, api, inputs)
        effects = () if backend == 'memory' else ('external_read', 'external_write', 'platform_input')
        self._stream_operation(call['node'], api, identity, inputs, effects)
        if api in ('builtins.open', 'io.open'):
            # A user opener receives the path and computed open flags. Flags
            # stay unresolved; source text is not evaluated to invent them.
            for name, callback in call['keywords']:
                if name == 'opener' and not (callback in self.literals and self.literals[callback] is None):
                    flags = self._derived_node('stream_open_flags', 'open_flags', call['node'])
                    for value in inputs:
                        self._edge(value, flags, 'stream_open_flags_input', False)
                    path = call['args'][0] if call['args'] else next(
                        (v for k, v in call['keywords'] if k == 'file'), None)
                    if path is None:
                        path = self._derived_node('stream_open_path', 'unresolved_file', call['node'])
                    event = self._derived_node('implicit_call', api + '.opener', call['node'])
                    self.calls.append({'node': event, 'function': callback, 'args': [path, flags],
                                       'keywords': [], 'starred': False, 'controls': [call['node']]})
                    self._edge(event, self.stream_states[identity], 'stream_opener_result', False)
                    self._unknown(call['node'], 'stream_opener_dispatch_summary_required')
        return True

    def _stream_attribute(self, receiver, identity, attribute, value, write):
        state = self.stream_states[identity]
        self._edge(state, value, 'stream_attribute_input', False)
        self._edge(receiver, value, 'stream_receiver', False)
        if write:
            self._edge(value, state, 'stream_attribute_mutation', False)
            self._unknown(value, 'stream_attribute_write_summary_required:' + attribute)
        elif attribute in ('buffer', 'raw'):
            child = self._stream_object(value, 'wrapper', 'stream.' + attribute, [receiver, state])
            self._edge(self.stream_states[child], state, 'stream_backing_mutation', False)
            self._unknown(value, 'stream_backing_dispatch_summary_required:' + attribute)
        elif attribute in ('read', 'read1', 'readline', 'readlines', 'readinto', 'readinto1',
                           'write', 'writelines', 'flush', 'close', 'seek', 'tell', 'truncate',
                           'fileno', 'isatty', 'readable', 'writable', 'seekable', 'getvalue',
                           'getbuffer', 'detach', '__enter__', '__exit__', '__iter__', '__next__'):
            self._seed(value, 'stream_method', attribute, identity)
            self._unknown(value, 'stream_receiver_dispatch_summary_required:' + attribute)
        elif attribute in ('closed', 'name', 'mode', 'encoding', 'errors', 'newlines'):
            self._stream_operation(value, 'stream.' + attribute, identity, [receiver],
                                   () if self.stream_metadata[identity]['backend'] == 'memory' else ('platform_input',))
        else:
            self._unknown(value, 'stream_attribute_summary_required:' + attribute)

    def _stream_method(self, call, method, identity):
        state = self.stream_states[identity]
        inputs = [call['function'], *call['args'], *(value for _, value in call['keywords'])]
        external = self.stream_metadata[identity]['backend'] != 'memory'
        effects = []
        if external and method in ('read', 'read1', 'readline', 'readlines', 'readinto', 'readinto1', '__next__'):
            effects.append('external_read')
        if external and method in ('write', 'writelines', 'flush', 'close', 'truncate', '__exit__'):
            effects.append('external_write')
        if external:
            effects.append('platform_input')
        if method in ('readinto', 'readinto1', 'getbuffer'):
            effects.append('buffer_mutation')
            self._unknown(call['node'], 'stream_mutated_buffer_alias_summary_required')
        self._stream_operation(call['node'], 'stream.' + method, identity, inputs, effects)
        # Include cursor, contents, buffer and closed-state mutations in every
        # later operation. This is flow-insensitive provenance, not a claim
        # that a closed stream can be read or a failed write was durable.
        self._edge(call['node'], state, 'stream_state_mutation', False)
        if method in ('__enter__', '__iter__'):
            self._seed(call['node'], 'stream_object', identity)
        elif method == 'detach':
            child = self._stream_object(call['node'], 'wrapper', 'stream.detach', [state])
            self._edge(self.stream_states[child], state, 'stream_backing_mutation', False)
        elif method == 'writelines':
            if call['args']:
                item = self._derived_node('stream_write_item', 'writelines_item', call['node'])
                self.iterations.append((call['args'][0], item))
                self._edge(item, call['node'], 'stream_write_item', False)
            self._unknown(call['node'], 'stream_writelines_iteration_summary_required')

    def _stream_protocols(self, references):
        for context in self.context_inventory:
            receiver = context['receiver']
            for kind, identity, _ in sorted(references.get(receiver, ())):
                if kind != 'stream_object':
                    continue
                if context['asynchronous']:
                    self._unknown(context['enter_node'], 'stream_async_context_summary_required')
                    continue
                entered, exited = context['enter_node'], context['exit_node']
                self._stream_operation(entered, 'stream.__enter__', identity, [receiver])
                self._seed(entered, 'stream_object', identity)
                self._stream_operation(exited, 'stream.__exit__', identity,
                                       [receiver, entered, *context['exception_nodes']],
                                       () if self.stream_metadata[identity]['backend'] == 'memory' else ('external_write', 'platform_input'))
                self._edge(exited, self.stream_states[identity], 'stream_state_mutation', False)
        for receiver, item in self.iterations:
            for kind, identity, _ in sorted(references.get(receiver, ())):
                if kind == 'stream_object':
                    self._stream_operation(item, 'stream.iteration', identity, [receiver],
                                           () if self.stream_metadata[identity]['backend'] == 'memory' else ('external_read', 'platform_input'))
                    self._edge(item, self.stream_states[identity], 'stream_state_mutation', False)
                    self._unknown(item, 'stream_iteration_lifecycle_summary_required')

    def _stream_escapes(self, references, slots, contained=None):
        if not self.stream_states:
            return
        cache = {}

        def contained_streams(value):
            if contained is not None:
                return contained(value, 'stream')
            origin = frozenset(references.get(value, ()))
            if origin in cache:
                return cache[origin]
            pending, seen, found = [value], set(), set()
            while pending:
                item = pending.pop()
                if item in seen:
                    continue
                seen.add(item)
                values = frozenset(references.get(item, ()))
                if values in cache:
                    found.update(cache[values])
                    continue
                for kind, identity, _ in values:
                    if kind == 'stream_object':
                        found.add(identity)
                    elif kind == 'container':
                        pending.append(self.members[identity])
                        if identity in self.container_keys:
                            pending.append(self.container_keys[identity])
                    elif kind == 'instance':
                        pending.extend(slot for (owner, _), slot in slots.items() if owner == identity)
            cache[origin] = found
            return found

        for call in self.calls:
            targets = references.get(call['function'], ())
            if targets and all(kind in ('function', 'bound') for kind, _, _ in targets):
                continue
            arguments = [*call['args'], *(value for _, value in call['keywords'])]
            for identity in sorted(set().union(*(contained_streams(value) for value in arguments))):
                state = self.stream_states[identity]
                for argument in arguments:
                    self._edge(argument, call['node'], 'stream_escape_argument', False)
                self._edge(state, call['node'], 'stream_escape_read', False)
                self._edge(call['node'], state, 'stream_escape_mutation', False)
                self._unknown(call['node'], 'stream_escape_effects_summary_required')

    def _json_result(self, node, identity):
        row = self.json_values[identity]
        self._seed(node, 'json_value', identity)
        self._seed(node, 'external_result', 'json.decoded_value')
        self._edge(row['value_node'], node, 'json_value_alternative')
        self._edge(row['state_node'], node, 'json_value_input', False)

    def _json_operation(self, node, api, inputs, identity=None):
        key = node, api, identity or ''
        if key not in self.json_operations:
            self.json_operations[key] = {'node': node, 'api': api, 'value_identity': identity,
                'inputs': set(), 'classification': 'conditional_possible_branch',
                'preconditions': ['authentic_stdlib_binding:json', 'argument_and_callback_selection_classified',
                                  'receiver_and_custom_class_dispatch_classified', 'successful_declared_api_call']}
        for value in inputs:
            self.json_operations[key]['inputs'].add(value)
            self._edge(value, node, 'json_input', False)
        self._unknown(node, 'json_effects_summary_required:' + api)
        self._unknown(node, 'stdlib_binding_summary_required:json')
        self._seed(node, 'external_result', api)

    def _json_implicit_call(self, origin, function, arguments, label, keywords=()):
        event = self._derived_node('implicit_call', label, origin)
        self.calls.append({'node': event, 'function': function, 'args': list(arguments),
                           'keywords': list(keywords), 'starred': False, 'controls': [origin]})
        return event

    def _json_io_call(self, origin, receiver, method, arguments):
        function = self._derived_node('json_io_method', method, origin)
        self.attributes.append((receiver, method, function, False))
        return self._json_implicit_call(origin, function, arguments, 'json.file.' + method)

    def _json_call(self, call, api):
        if api not in ('json.loads', 'json.load', 'json.dumps', 'json.dump'):
            return False
        node = call['node']
        inputs = [call['function'], *call['args'], *(v for _, v in call['keywords'])]
        keywords = dict(call['keywords'])
        self._json_operation(node, api, inputs)
        if call['starred'] or None in keywords:
            self._unknown(node, 'json_expanded_argument_summary_required')
        value = call['args'][0] if call['args'] else keywords.get('fp' if api == 'json.load' else ('s' if api == 'json.loads' else 'obj'))
        if value is None:
            value = self._derived_node('json_argument', 'unresolved_input', node)
            self._unknown(node, 'json_argument_binding_summary_required')
        if api == 'json.load':
            value = self._json_io_call(node, value, 'read', [])
            self._edge(value, node, 'json_file_input', False)
        decoding = api in ('json.loads', 'json.load')
        identity = None
        if decoding:
            identity = '%s:%s' % (node, api)
            state = self._derived_node('json_state', identity, node)
            leaf = self._derived_node('json_decoded_value', 'possible_root_or_member', node)
            key = self._derived_node('json_decoded_key', 'object_key', node)
            self.json_values[identity] = {'node': node, 'state_node': state, 'value_node': leaf, 'key_node': key}
            self._edge(value, state, 'json_parse_input', False)
            self._edge(state, leaf, 'json_decoded_input', False)
            self._edge(state, key, 'json_decoded_input', False)
            self._seed(leaf, 'json_value', identity)
            self._seed(leaf, 'external_result', 'json.decoded_member')
            self._seed(key, 'external_result', 'json.decoded_key')
            self._json_result(node, identity)
        callback_names = ('object_pairs_hook', 'object_hook', 'parse_int', 'parse_float', 'parse_constant') if decoding else ('default',)
        for name in callback_names:
            callback = keywords.get(name)
            if callback is None or (callback in self.literals and self.literals[callback] is None):
                continue
            argument = self._derived_node('json_callback_argument', name, node)
            self._edge(value, argument, 'json_callback_input', False)
            if name == 'object_pairs_hook':
                pairs = self._container_result(argument, 'list', 'json-object-pairs')
                pair = self._container_result(argument, 'tuple', 'json-object-pair')
                self._seed(argument, 'container', pairs)
                self._seed(self.members[pairs], 'container', pair)
                self._edge(self.json_values[identity]['key_node'], self._container_slot(pair, 0, argument), 'json_pair_key')
                self._edge(self.json_values[identity]['value_node'], self._container_slot(pair, 1, argument), 'json_pair_value')
            elif name == 'object_hook':
                self._json_result(argument, identity)
            elif name == 'default':
                self.json_encoding_members.add((value, argument))
            else:
                self._seed(argument, 'external_result', 'json.numeric_lexeme')
            event = self._json_implicit_call(node, callback, [argument], api + '.' + name)
            condition = ('object_pairs_hook_absent_or_None' if name == 'object_hook' else
                         'ordinary_decoder_selects_' + name if decoding else 'ordinary_encoder_requires_default')
            self.json_callbacks.append({'node': node, 'api': api, 'name': name, 'callback_node': event,
                                        'function_node': callback, 'argument_node': argument,
                                        'selection_precondition': condition, 'return_identity': decoding})
            self._edge(event, node, 'json_callback_result', decoding)
            if decoding:
                self._edge(event, self.json_values[identity]['value_node'], 'json_member_callback_result')
            self._unknown(node, 'json_callback_selection_summary_required:' + name)
        custom = keywords.get('cls')
        custom_result = None
        if custom is not None and not (custom in self.literals and self.literals[custom] is None):
            constructor_keywords = [(k, v) for k, v in call['keywords'] if k not in ('cls', 's', 'obj', 'fp')]
            instance = self._json_implicit_call(node, custom, [], api + '.cls', constructor_keywords)
            method = 'decode' if decoding else ('iterencode' if api == 'json.dump' else 'encode')
            custom_result = self._json_io_call(node, instance, method, [value])
            self._edge(custom_result, node, 'json_custom_class_result', api != 'json.dump')
            if decoding:
                self._edge(custom_result, self.json_values[identity]['value_node'], 'json_custom_value_result')
            self._unknown(node, 'json_custom_class_dispatch_summary_required')
        if api == 'json.dump':
            destination = call['args'][1] if len(call['args']) > 1 else keywords.get('fp')
            if destination is None:
                destination = self._derived_node('json_argument', 'unresolved_output', node)
                self._unknown(node, 'json_argument_binding_summary_required')
            chunk = self._derived_node('json_encoded_chunk', 'encoded_text', node)
            self._seed(chunk, 'external_result', 'json.encoded_text')
            self._edge(node, chunk, 'json_encoded_input', False)
            if custom_result is not None:
                self.iterations.append((custom_result, chunk))
            written = self._json_io_call(node, destination, 'write', [chunk])
            self._edge(written, node, 'json_file_output_effect', False)
        return True

    def _json_attribute(self, receiver, identity, attribute, value, write):
        row = self.json_values[identity]
        self._edge(row['state_node'], value, 'json_attribute_input', False)
        self._edge(receiver, value, 'json_receiver', False)
        if write:
            self._edge(value, row['state_node'], 'json_attribute_mutation', False)
            self._unknown(value, 'json_attribute_write_summary_required:' + attribute)
        elif attribute in ('get', 'keys', 'values', 'items', 'copy', 'pop', 'setdefault',
                           'update', 'clear', '__getitem__', '__setitem__'):
            self._seed(value, 'json_method', attribute, identity)
            self._unknown(value, 'json_receiver_dispatch_summary_required:' + attribute)
        else:
            self._unknown(value, 'json_attribute_summary_required:' + attribute)

    def _json_method(self, call, method, identity):
        row = self.json_values[identity];node = call['node']
        self._json_operation(node, 'json_value.' + method,
                             [call['function'], row['state_node'], *call['args'], *(v for _, v in call['keywords'])], identity)
        if method in ('get', 'pop', '__getitem__', 'setdefault', 'copy'):
            self._json_result(node, identity)
            if method in ('get', 'pop', 'setdefault') and len(call['args']) > 1:
                self._edge(call['args'][1], node, 'json_missing_default')
        elif method in ('keys', 'values', 'items'):
            output = self._container_result(node, 'view', 'json-' + method)
            self._seed(node, 'container', output)
            if method == 'items':
                pair = self._container_result(node, 'tuple', 'json-item-pair')
                self._seed(self.members[output], 'container', pair)
                self._edge(row['key_node'], self._container_slot(pair, 0, node), 'json_pair_key')
                self._edge(row['value_node'], self._container_slot(pair, 1, node), 'json_pair_value')
            else:
                self._edge(row['key_node'] if method == 'keys' else row['value_node'], self.members[output], 'json_view_value')
        if method in ('pop', 'setdefault', 'update', 'clear', '__setitem__'):
            self._edge(node, row['state_node'], 'json_state_mutation', False)
            values = call['args'][1:] if method in ('setdefault', '__setitem__') else call['args'] if method == 'update' else []
            for value in values:
                self._edge(value, row['value_node'], 'json_written_value')
            self._unknown(node, 'json_mutation_alias_summary_required')

    def _json_protocols(self, references, slots, contained=None):
        if not self.json_values and not self.json_encoding_members:
            return
        for receiver, selector, value, write in self.subscripts:
            for kind, identity, _ in sorted(references.get(receiver, ())):
                if kind != 'json_value':
                    continue
                row = self.json_values[identity]
                token = ('subscript', receiver, selector, value, write, identity,
                         row['state_node'], row['value_node'])
                if token in self.json_protocol_links:
                    continue
                self.json_protocol_links.add(token)
                self._json_operation(value, 'json_value.subscript', [receiver, selector, row['state_node']], identity)
                if write:
                    self._edge(value, row['value_node'], 'json_written_value')
                    self._edge(value, row['state_node'], 'json_state_mutation', False)
                else:
                    self._json_result(value, identity)
                self._unknown(value, 'json_selector_and_mutation_summary_required')
        for receiver, value in self.iterations:
            for kind, identity, _ in sorted(references.get(receiver, ())):
                if kind == 'json_value':
                    row = self.json_values[identity]
                    token = ('iteration', receiver, value, identity, row['state_node'], row['value_node'])
                    if token in self.json_protocol_links:
                        continue
                    self.json_protocol_links.add(token)
                    self._json_operation(value, 'json_value.iteration', [receiver, self.json_values[identity]['state_node']], identity)
                    self._json_result(value, identity)
                    self._unknown(value, 'json_iteration_summary_required')
        for receiver, target in sorted(self.json_encoding_members):
            pending, seen = [receiver], set()
            while pending:
                item = pending.pop()
                if item in seen:
                    continue
                seen.add(item)
                self._edge(item, target, 'json_encoding_candidate')
                for kind, identity, _ in references.get(item, ()):
                    if kind == 'container':
                        pending.append(self.members[identity])
                    elif kind == 'json_value':
                        pending.append(self.json_values[identity]['value_node'])
        # All calls in this round see the same reference snapshot. Reuse a
        # containment result for equal starting aliases, but rebuild the cache
        # next round so newly written fields and container members are visited.
        cache, instance_slots = {}, {}
        for (owner, _), slot in slots.items():
            instance_slots.setdefault(owner, []).append(slot)

        def contained_json(value):
            if contained is not None:
                return contained(value, 'json')
            origin = frozenset(references.get(value, ()))
            if origin in cache:
                return cache[origin]
            pending, seen, found = [value], set(), set()
            while pending:
                item = pending.pop()
                if item in seen:
                    continue
                seen.add(item)
                values = frozenset(references.get(item, ()))
                if values in cache:
                    found.update(cache[values])
                    continue
                for kind, identity, _ in values:
                    if kind == 'json_value':
                        found.add(identity)
                    elif kind == 'container':
                        pending.append(self.members[identity])
                        if identity in self.container_keys:
                            pending.append(self.container_keys[identity])
                    elif kind == 'instance':
                        pending.extend(instance_slots.get(identity, ()))
            cache[origin] = found
            return found

        for call in self.calls:
            targets = references.get(call['function'], ())
            if targets and all(kind in ('function', 'bound') for kind, _, _ in targets):
                continue
            arguments = [*call['args'], *(v for _, v in call['keywords'])]
            found = set().union(*(contained_json(value) for value in arguments))
            for identity in sorted(found):
                row = self.json_values[identity]
                self._edge(row['state_node'], call['node'], 'json_escape_read', False)
                for argument in arguments:
                    self._edge(argument, call['node'], 'json_escape_argument', False)
                self._edge(call['node'], row['state_node'], 'json_escape_mutation', False)
                self._unknown(call['node'], 'json_escape_effects_summary_required')

    def _primitive_effects(self):
        """Prove exact builtin operations without trusting a may-alias set.

        All reference producers must be closed before a variable gets a type.
        A known assignment plus an unresolved assignment therefore stays open.
        Parameters and field/element reads need separate contracts. Local
        returns require all represented exits and a closed callable identity.
        No candidate expression is evaluated. Result types are conservative
        sets, including the possible numeric promotions of two-argument pow.
        """
        scalar = {'NoneType', 'bool', 'int', 'float', 'complex', 'str', 'bytes', 'ellipsis'}
        real, numeric = {'bool', 'int', 'float'}, {'bool', 'int', 'float', 'complex'}
        integral = {'bool', 'int'}
        sized = {'str', 'bytes', 'list', 'tuple', 'dict', 'set', 'frozenset', 'range',
                 'dict_keys', 'dict_values', 'dict_items'}
        truth = scalar | sized
        incoming = {}
        for source, target, _, reference in self.edges:
            if reference:
                incoming.setdefault(target, set()).add(source)
        parameters = {node for definition in self.definitions.values() for node in definition['parameters']}
        calls = {call['node']: call for call in self.calls}
        return_slots = {definition['return']: (identity, definition)
                        for identity, definition in self.definitions.items() if definition['kind'] == 'function'}
        reads, iterations, attributes, method_receivers, hash_method_receivers = {}, {}, {}, {}, {}
        for receiver, method, result, write in self.attributes:
            if not write:
                attributes.setdefault(result, set()).add((receiver, method))
        for receiver, selector, value, write in self.subscripts:
            if not write:
                reads.setdefault(value, set()).add((receiver, selector))
        for receiver, value in self.iterations:
            iterations.setdefault(value, set()).add(receiver)
        facts, effects, return_facts, local_call_facts = {}, {}, {}, {}
        # These exact result types follow the CPython builtin wrappers on
        # both supported runtimes. They hold only after a successful call.
        # Argument conversion, callbacks, mutation and platform input remain
        # separate obligations. str/repr/ascii and abs are deliberately absent:
        # their object hooks can return subclasses or arbitrary objects.
        builtin_return_types = {
            'len': 'int', 'hash': 'int', 'id': 'int', 'ord': 'int', 'float': 'float',
            'bool': 'bool', 'callable': 'bool', 'hasattr': 'bool',
            'isinstance': 'bool', 'issubclass': 'bool', 'all': 'bool', 'any': 'bool',
            'chr': 'str', 'hex': 'str', 'oct': 'str', 'range': 'range',
            'list': 'list', 'tuple': 'tuple', 'dict': 'dict', 'set': 'set', 'frozenset': 'frozenset'}

        def types(node):
            values = facts.get(node, ())
            return {value[5:] for value in values} if values and all(value.startswith('type:') for value in values) else set()

        def typed(names):
            return {'type:' + name for name in names}

        def binary(operation, left, right):
            if left in numeric and right in numeric:
                promoted = 'complex' if 'complex' in (left, right) else ('float' if 'float' in (left, right) else 'int')
                if operation in ('Add', 'Sub', 'Mult'):
                    return {promoted}
                if operation == 'Div':
                    return {'complex' if promoted == 'complex' else 'float'}
                if operation in ('FloorDiv', 'Mod') and left in real and right in real:
                    return {promoted}
                if operation == 'Pow':
                    return {'complex'} if promoted == 'complex' else (
                        {'int', 'float'} if promoted == 'int' else {'float', 'complex'})
                if left in integral and right in integral:
                    if operation in ('LShift', 'RShift'):
                        return {'int'}
                    if operation in ('BitAnd', 'BitOr', 'BitXor'):
                        return {'bool' if left == right == 'bool' else 'int'}
            if operation == 'Add' and left == right and left in {'str', 'bytes'}:
                return {left}
            if operation == 'Mult':
                if left in {'str', 'bytes'} and right in integral:
                    return {left}
                if right in {'str', 'bytes'} and left in integral:
                    return {right}
            # Percent formatting can invoke mapping, conversion and buffer
            # protocols. It is not numeric remainder when the left is text.
            return set()

        def operator_result(family, operations, operands):
            operand_types = [types(node) for node in operands]
            if family == 'Slice':
                # Creating a slice does not invoke its bounds' __index__.
                return {'slice'}
            if family == 'Compare':
                for index, operation in enumerate(operations):
                    if operation in ('Is', 'IsNot'):
                        continue
                    left, right = operand_types[index:index + 2]
                    if not left or not right:
                        return set()
                    if operation in ('Eq', 'NotEq') and left <= scalar and right <= scalar:
                        continue
                    if operation in ('Lt', 'LtE', 'Gt', 'GtE') and all(
                            (a in real and b in real) or (a == b and a in {'str', 'bytes'})
                            for a in left for b in right):
                        continue
                    if operation in ('In', 'NotIn') and left == right == {'str'}:
                        continue
                    if operation in ('In', 'NotIn') and right == {'bytes'} and left <= {'bytes', 'int', 'bool'}:
                        continue
                    return set()
                return {'bool'}
            if not all(operand_types):
                return set()
            if family in ('BinOp', 'AugAssign'):
                output = set()
                for left in operand_types[0]:
                    for right in operand_types[1]:
                        pair = binary(operations[0], left, right)
                        if not pair:
                            return set()
                        output.update(pair)
                return output
            if family == 'UnaryOp':
                values = operand_types[0]
                if operations == ['Not'] and values <= truth:
                    return {'bool'}
                if operations[0] in ('UAdd', 'USub') and values <= numeric:
                    return {'int' if value == 'bool' else value for value in values}
                if operations == ['Invert'] and values <= integral:
                    # ~bool is deprecated and rejected by newer Python. A
                    # successful result, where supported, still has int type.
                    return {'int'}
            if family == 'FormattedValue' and operand_types[0] <= scalar and operations[0] in ('-1', '97', '114', '115'):
                if len(operand_types) == 1 or operand_types[1] == {'str'}:
                    return {'str'}
            if family == 'JoinedStr' and all(values == {'str'} for values in operand_types):
                return {'str'}
            return set()

        def builtin_result(call):
            targets = facts.get(call['function'], set())
            if len(targets) != 1:
                return set(), None
            target = next(iter(targets))
            if not target.startswith('external:builtins.'):
                return set(), None
            name = target[len('external:builtins.'):]
            returned = typed({builtin_return_types[name]}) if name in builtin_return_types else set()
            if returned:
                return_facts[call['node']] = {
                    'node': call['node'], 'callee': 'builtins.' + name,
                    'inputs': [call['function'], *call['args'], *(value for _, value in call['keywords'])],
                    'output_types': [builtin_return_types[name]], 'condition': 'successful_return'}
                if name == 'float':
                    return_facts[call['node']]['preconditions'] = ['authentic_builtin_binding:float']
                    self._unknown(call['node'], 'builtin_binding_summary_required:float')
            if call['starred'] or call['keywords']:
                return returned, None
            args = call['args']
            values = [types(node) for node in args]
            if name in ('list', 'tuple', 'dict', 'set', 'frozenset') and not args:
                return typed({name}), name
            if name in ('list', 'tuple') and len(args) == 1 and values[0] and values[0] <= sized:
                # Exact builtin iteration/length do not dispatch element
                # hooks. Contents still flow through _builtin_container.
                return typed({name}), name
            if name == 'type' and len(args) == 1:
                # The returned class can have a custom metaclass. Do not
                # infer exact type, truth, equality or callable semantics.
                return {'runtime_class'}, name
            if name == 'range' and 1 <= len(args) <= 3 and all(value and value <= integral for value in values):
                return typed({'range'}), name
            if name in ('bool', 'str') and not args:
                return typed({name}), name
            if len(args) != 1 or not values[0]:
                return returned, None
            value = values[0]
            output = set()
            if name == 'len' and value <= sized:
                output = {'int'}
            elif name == 'bool' and value <= truth:
                output = {'bool'}
            elif name in ('str', 'repr', 'ascii') and value <= scalar:
                output = {'str'}
            elif name == 'abs' and value <= numeric:
                output = {'float' if item == 'complex' else ('int' if item == 'bool' else item) for item in value}
            elif name == 'ord' and value <= {'str', 'bytes'}:
                output = {'int'}
            elif name in ('chr', 'hex', 'oct') and value <= integral:
                output = {'str'}
            return typed(output) if output else returned, name if output else None

        container_methods = {
            'list': {'append': 'NoneType', 'insert': 'NoneType', 'extend': 'NoneType',
                     'copy': 'list', 'reverse': 'NoneType'},
            'dict': {'keys': 'dict_keys', 'values': 'dict_values', 'items': 'dict_items'}}

        def container_result(call):
            targets = facts.get(call['function'], set())
            if not targets or any(target not in method_receivers for target in targets):
                return set(), None
            bindings = [method_receivers[target] for target in sorted(targets)]
            methods = {(kind, method) for kind, method, _ in bindings}
            if len(methods) != 1:
                return set(), None
            kind, method = next(iter(methods))
            receivers = sorted({receiver for _, _, receiver in bindings})
            name = kind + '.' + method
            output = container_methods[kind][method]
            obligation = 'container_element_protocol_summary_required:' + name
            inputs = [call['function'], *receivers, *call['args'], *(value for _, value in call['keywords'])]
            return_facts[call['node']] = {
                'node': call['node'], 'callee': name, 'inputs': inputs, 'output_types': [output],
                'condition': 'successful_return', 'effect_obligation': obligation}
            returned = typed({output})
            if call['starred'] or call['keywords']:
                return returned, None
            args = call['args']
            accepted = ((method in ('copy', 'reverse', 'keys', 'values', 'items') and not args)
                        or (method == 'append' and len(args) == 1)
                        or (method == 'insert' and len(args) == 2 and types(args[0]) and types(args[0]) <= integral)
                        or (method == 'extend' and len(args) == 1 and types(args[0]) and types(args[0]) <= sized))
            if not accepted:
                return returned, None
            return returned, {'node': call['node'], 'operation': name, 'inputs': inputs,
                              'output_types': [output], 'effect_obligation': obligation,
                              'receiver_nodes': receivers,
                              'mutation': 'retains_elements' if method in ('append', 'insert', 'extend') else (
                                  'reorders_elements' if method == 'reverse' else 'none')}

        def hash_result(call):
            targets = facts.get(call['function'], set())
            if len(targets) == 1 and next(iter(targets)) in ('external:hashlib.sha256', 'external:hashlib.sha1'):
                algorithm = next(iter(targets)).split('.')[-1]
                identity = '%s:%s' % (call['node'], algorithm)
                returned = {'hash_object:' + identity}
                operation = 'hashlib.' + algorithm
                obligation = 'external_api_summary_required:' + operation
                inputs = [call['function'], *call['args'], *(value for _, value in call['keywords'])]
                accepted = (not call['starred'] and len(call['args']) <= 1
                            and all(types(value) == {'bytes'} for value in call['args'])
                            and all(name == 'usedforsecurity' and types(value) == {'bool'} for name, value in call['keywords']))
            elif targets and all(target in hash_method_receivers for target in targets):
                bindings = [hash_method_receivers[target] for target in sorted(targets)]
                methods = {method for method, _, _ in bindings}
                if len(methods) != 1:
                    return set(), None
                method = next(iter(methods))
                operation = 'hash.' + method
                obligation = 'hash_method_summary_required:' + method
                inputs = [call['function'], *sorted({receiver for _, _, receiver in bindings}),
                          *call['args'], *(value for _, value in call['keywords'])]
                if method == 'copy':
                    returned = {'hash_object:%s:%s' % (call['node'], self.hash_kinds[identity]) for _, identity, _ in bindings}
                else:
                    returned = typed({{'digest': 'bytes', 'hexdigest': 'str', 'update': 'NoneType'}[method]})
                accepted = (not call['starred'] and not call['keywords'] and (
                    (method != 'update' and not call['args']) or
                    (method == 'update' and len(call['args']) == 1 and types(call['args'][0]) == {'bytes'})))
            else:
                return set(), None
            output_types = sorted(value[5:] for value in returned if value.startswith('type:'))
            preconditions = ['authentic_stdlib_binding:hashlib']
            return_facts[call['node']] = {'node': call['node'], 'callee': operation, 'inputs': inputs,
                                          'output_types': output_types, 'output_facts': sorted(returned),
                                          'condition': 'successful_return', 'preconditions': preconditions,
                                          'effect_obligation': obligation}
            effect = {'node': call['node'], 'operation': operation, 'inputs': inputs,
                      'output_types': output_types, 'output_facts': sorted(returned),
                      'effect_obligation': obligation, 'preconditions': preconditions} if accepted else None
            return returned, effect

        def local_result(call):
            targets = facts.get(call['function'], set())
            if not targets or any(not target.startswith('function:') for target in targets):
                return set()
            identities = sorted(target[len('function:'):] for target in targets)
            slots = [self.definitions[identity]['return'] for identity in identities]
            if not all(slot in facts for slot in slots):
                return set()
            values = set()
            for slot in slots:
                values.update(facts[slot])
            local_call_facts[call['node']] = {'node': call['node'], 'callee_node': call['function'],
                                            'functions': identities, 'return_slots': slots,
                                            'output_facts': sorted(values), 'condition': 'successful_return'}
            return values

        def json_result(call):
            # Successful native result types do not prove callback, IO or
            # binding effects. In particular an input hook could replace a
            # cached decoder while json.loads is still running. Retain that
            # stability precondition on every fact derived from this result.
            targets = facts.get(call['function'], set())
            if len(targets) != 1:
                return set()
            target = next(iter(targets))
            if target not in ('external:json.loads', 'external:json.load',
                              'external:json.dumps', 'external:json.dump'):
                return set()
            if call['starred'] or any(name is None for name, _ in call['keywords']):
                return set()
            api = target[len('external:'):]
            keywords = dict(call['keywords'])
            if len(keywords) != len(call['keywords']):
                return set()
            decoding = api in ('json.loads', 'json.load')
            data_names = ('s',) if api == 'json.loads' else ('fp',) if api == 'json.load' else (
                ('obj', 'fp') if api == 'json.dump' else ('obj',))
            options = {'cls', 'object_hook', 'object_pairs_hook', 'parse_int', 'parse_float',
                       'parse_constant', 'strict'} if decoding else {
                           'skipkeys', 'ensure_ascii', 'check_circular', 'allow_nan', 'cls',
                           'indent', 'separators', 'default', 'sort_keys'}
            if (len(call['args']) > len(data_names) or not set(keywords) <= options | set(data_names)
                    or any(name in keywords for name in data_names[:len(call['args'])])
                    or any(name not in keywords for name in data_names[len(call['args']):])):
                return set()
            def absent_or_none(name):
                return name not in keywords or types(keywords[name]) == {'NoneType'}
            preconditions = ['authentic_stdlib_binding:json']
            callback_results, result_dependencies = [], set()

            def decode_hook(name, native):
                if absent_or_none(name):
                    return {native}
                selected = facts.get(keywords[name], set())
                if not selected or any(not value.startswith('function:') for value in selected):
                    return None
                outputs, functions = set(), []
                for target in sorted(selected):
                    identity = target[len('function:'):]
                    definition = self.definitions[identity]
                    inventory = definition['return_inventory']
                    if not inventory['supported'] or inventory['suspension'] is not None:
                        return None
                    never_returns = not definition['return_values'] and not inventory['falls_through']
                    returned = set() if never_returns else types(definition['return'])
                    if not returned and not never_returns:
                        return None
                    outputs.update(returned)
                    result_dependencies.add(definition['return'])
                    functions.append({'function': identity, 'return_slot': definition['return'],
                                      'output_types': sorted(returned), 'never_returns': never_returns})
                callback_results.append({'name': name, 'callback_node': keywords[name], 'functions': functions,
                                         'output_types': sorted(outputs), 'condition': 'successful_callback_return'})
                return outputs

            if decoding:
                if not absent_or_none('cls'):
                    return set()
                # These callbacks replace only their corresponding decoded
                # root kinds. Arrays, strings, booleans and null still have
                # native root types. Nested member identities stay separate.
                object_hook = 'object_hook' if absent_or_none('object_pairs_hook') else 'object_pairs_hook'
                branches = [decode_hook(object_hook, 'dict'), decode_hook('parse_int', 'int'),
                            decode_hook('parse_float', 'float'), decode_hook('parse_constant', 'float')]
                if any(branch is None for branch in branches):
                    return set()
                outputs = {'NoneType', 'bool', 'list', 'str'}.union(*branches)
                preconditions.append('native_json_decoder_bindings_stable_during_call')
                self._unknown(call['node'], 'json_binding_stability_summary_required:decoder')
                if callback_results:
                    preconditions.append('json_callback_bodies_stable_during_call')
                    self._unknown(call['node'], 'json_callback_body_stability_summary_required')
            elif api == 'json.dumps':
                if not absent_or_none('cls'):
                    return set()
                outputs = {'str'}
                preconditions.append('native_json_encoder_bindings_stable_during_call')
                self._unknown(call['node'], 'json_binding_stability_summary_required:encoder')
            else:
                # dump ignores write results and returns None even with a
                # custom encoder. Its output chunks and writer effects stay
                # in the separate JSON/stream/callback inventories.
                outputs = {'NoneType'}
            return_facts[call['node']] = {
                'node': call['node'], 'callee': api,
                'inputs': [call['function'], *call['args'], *(value for _, value in call['keywords']),
                           *sorted(result_dependencies)],
                'output_types': sorted(outputs), 'condition': 'successful_return',
                'result_contract': 'json_successful_result.v2', 'callback_results': callback_results,
                'preconditions': preconditions, 'effect_obligation': 'json_effects_summary_required:' + api}
            return typed(outputs)

        transparent = {'symbol', 'name_read', 'assignment_value', 'controlled_assignment',
                       'NamedExpr', 'IfExp', 'BoolOp'}
        literal_containers = {'List': 'list', 'Tuple': 'tuple', 'Set': 'set', 'Dict': 'dict',
                              'ListComp': 'list', 'SetComp': 'set', 'DictComp': 'dict'}
        guarded = {}

        def propagate():
            # Edges are now fixed. Facts only grow. Requiring every predecessor
            # prevents late or unresolved alternatives from disappearing.
            for _ in range(len(self.nodes) + 1):
                changed = False
                for node in self.nodes:
                    number, kind = node['id'], node['kind']
                    value, effect = set(), None
                    if number in guarded:
                        value = typed(guarded[number]['output_types'])
                    elif number in self.literals:
                        value = typed({type(self.literals[number]).__name__})
                    elif kind in literal_containers:
                        value = typed({literal_containers[kind]})
                        construction = self.container_constructions.get(number)
                        if construction is not None and not construction['expanded']:
                            keys, values = construction['keys'], construction['values']
                            accepted = False
                            if construction['kind'] == 'dict' and all(key in self.literals for key in keys):
                                literal_keys = [self.literals[key] for key in keys]
                                # Distinct builtin literal keys neither dispatch
                                # custom hash/equality nor replace a value whose
                                # finalizer could run during construction.
                                accepted = (all(type(key).__name__ in scalar for key in literal_keys)
                                            and len(set(literal_keys)) == len(literal_keys))
                            elif construction['kind'] == 'set':
                                accepted = all(types(item) and types(item) <= scalar for item in values)
                            if accepted:
                                effect = {'node': number, 'operation': 'literal_' + construction['kind'],
                                          'inputs': keys + values, 'output_types': [construction['kind']],
                                          'effect_obligation': 'container_construction_protocol_summary_required:' + construction['kind']}
                    elif number in self.operators:
                        family, operations, operands = self.operators[number]
                        output = operator_result(family, operations, operands)
                        value = typed(output)
                        if output:
                            effect = {'node': number, 'operation': family, 'operators': operations,
                                      'inputs': operands, 'output_types': sorted(output),
                                      'identity_dependency': any(item in ('Is', 'IsNot') for item in operations)}
                    elif number in calls:
                        call = calls[number]
                        value, builtin = builtin_result(call)
                        if builtin:
                            effect = {'node': number, 'operation': 'builtins.' + builtin,
                                      'inputs': [call['function'], *call['args']],
                                      'output_types': sorted(item[5:] if item.startswith('type:') else item for item in value)}
                        if not value:
                            value, method_effect = container_result(call)
                            if method_effect is not None:
                                effect = method_effect
                        if not value:
                            value, hash_effect = hash_result(call)
                            if hash_effect is not None:
                                effect = hash_effect
                        if not value:
                            value = json_result(call)
                        if not value:
                            value = local_result(call)
                    elif number in attributes:
                        receivers = set()
                        for receiver, method in attributes[number]:
                            names = types(receiver)
                            receiver_facts = facts.get(receiver, set())
                            if receiver_facts == {'external:hashlib'} and method in ('sha256', 'sha1'):
                                value.add('external:hashlib.' + method)
                                self._unknown(number, 'stdlib_binding_summary_required:hashlib')
                            elif receiver_facts == {'external:json'} and method in ('loads', 'load', 'dumps', 'dump'):
                                value.add('external:json.' + method)
                                self._unknown(number, 'stdlib_binding_summary_required:json')
                            elif receiver_facts and all(item.startswith('hash_object:') for item in receiver_facts) and method in (
                                    'update', 'digest', 'hexdigest', 'copy'):
                                for item in receiver_facts:
                                    identity = item[len('hash_object:'):]
                                    token = 'hash_method:%s@%s@%s' % (method, identity, receiver)
                                    hash_method_receivers[token] = method, identity, receiver
                                    value.add(token)
                            elif not names or any(method not in container_methods.get(name, {}) for name in names):
                                value = set()
                                break
                            else:
                                for name in names:
                                    token = 'builtin_method:%s.%s@%s' % (name, method, receiver)
                                    method_receivers[token] = name, method, receiver
                                    value.add(token)
                            receivers.add(receiver)
                        if value:
                            method = next(iter(attributes[number]))[1]
                            effect = {'node': number, 'operation': 'builtin_method_binding',
                                      'inputs': sorted(receivers), 'output_types': [],
                                      'output_facts': sorted(value),
                                      'effect_obligation': 'attribute_receiver_summary_required:' + method}
                            if value & {'external:json.' + name for name in ('loads', 'load', 'dumps', 'dump')}:
                                effect['preconditions'] = ['authentic_stdlib_binding:json']
                    elif number in return_slots:
                        _, definition = return_slots[number]
                        inventory = definition['return_inventory']
                        values = definition['return_values']
                        if inventory['supported'] and inventory['suspension'] is None and values and all(item in facts for item in values):
                            for item in values:
                                value.update(facts[item])
                    elif number in reads:
                        inputs, complete, result_known, receiver_union = set(), True, True, set()
                        for receiver, selector in reads[number]:
                            receiver_types, selector_types = types(receiver), types(selector)
                            output = set()
                            scalar_index = selector_types and selector_types <= integral
                            slice_index = selector in self.slices and all(types(item) and types(item) <= integral | {'NoneType'}
                                                                          for item in self.slices[selector])
                            if not receiver_types or not receiver_types <= {'str', 'bytes', 'range', 'list', 'tuple'} or not (
                                    scalar_index or slice_index):
                                complete = False
                                break
                            if slice_index:
                                output = receiver_types
                            elif receiver_types <= {'str', 'bytes', 'range'}:
                                output = {'str' if item == 'str' else 'int' for item in receiver_types}
                            else:
                                # Exact sequence access can be closed even when
                                # its element type still needs a content contract.
                                result_known = False
                            value.update(typed(output))
                            inputs.update((receiver, selector))
                            receiver_union.update(receiver_types)
                        if not complete or not result_known:
                            value = set()
                        if complete:
                            effect = {'node': number, 'operation': 'immutable_sequence_subscript' if receiver_union <= {
                                'str', 'bytes', 'range'} else 'builtin_sequence_subscript',
                                      'inputs': sorted(inputs), 'output_types': sorted(item[5:] for item in value),
                                      'effect_obligation': 'subscript_receiver_summary_required'}
                    elif number in iterations:
                        complete, result_known, receiver_union = True, True, set()
                        for receiver in iterations[number]:
                            receiver_types = types(receiver)
                            if not receiver_types or not receiver_types <= sized:
                                complete = False
                                break
                            if receiver_types <= {'str', 'bytes', 'range', 'dict_items'}:
                                value.update(typed({'str' if item == 'str' else ('tuple' if item == 'dict_items' else 'int')
                                                   for item in receiver_types}))
                            else:
                                result_known = False
                            receiver_union.update(receiver_types)
                        if not complete or not result_known:
                            value = set()
                        if complete:
                            effect = {'node': number, 'operation': 'immutable_sequence_iteration' if receiver_union <= {
                                'str', 'bytes', 'range'} else 'builtin_container_iteration',
                                      'inputs': sorted(iterations[number]), 'output_types': sorted(item[5:] for item in value),
                                      'effect_obligation': 'iteration_receiver_summary_required'}
                    elif kind in transparent and number not in parameters:
                        predecessors = incoming.get(number, set())
                        seeds = self.seeds.get(number, set())
                        # Seeded imports/builtins retain their exact identity.
                        # Unknown leaf symbols and partially known joins stay open.
                        if (predecessors or seeds) and all(source in facts for source in predecessors):
                            value = {tag + ':' + identity for tag, identity, _ in seeds
                                     if tag in ('external', 'module', 'function', 'class')}
                            if len(value) == len(seeds):
                                for source in predecessors:
                                    value.update(facts[source])
                            else:
                                value = set()
                    elif kind in ('function_definition', 'class_definition'):
                        value = {tag + ':' + identity for tag, identity, _ in self.seeds.get(number, ())}
                    if value and not value <= facts.get(number, set()):
                        facts.setdefault(number, set()).update(value)
                        changed = True
                    if effect is not None:
                        effects[number] = effect
                if not changed:
                    break
            else:
                raise ValueError('lcer.source_graph_did_not_converge')
        propagate()
        guard_records = PythonSuccessfulTypeGuards(self, facts).analyze()
        if guard_records:
            guarded.update({row['node']: row for row in guard_records})
            # Rebuild the exact-type solution. Unioning a narrower fact into
            # the old solution would leave broad return types in dependents.
            facts.clear()
            effects.clear()
            return_facts.clear()
            local_call_facts.clear()
            method_receivers.clear()
            hash_method_receivers.clear()
            propagate()
        local_type_records = []
        for _ in range(len(self.nodes) + 1):
            selected = PythonSuccessfulLocalTypes(self, facts).analyze()
            if selected == local_type_records:
                break
            local_type_records = selected
            guarded.clear()
            guarded.update({row['node']: row for row in guard_records})
            guarded.update({row['node']: row for row in local_type_records})
            facts.clear()
            effects.clear()
            return_facts.clear()
            local_call_facts.clear()
            method_receivers.clear()
            hash_method_receivers.clear()
            propagate()
        else:
            raise ValueError('lcer.source_graph_did_not_converge')
        # A conditional native result cannot silently become an unconditional
        # assignment, local return, operator or truth fact. Propagate only
        # through the dependencies used by this exact-type proof, retaining
        # all producers at joins. This does not remove any may-flow edge.
        dependencies = {number: set(incoming.get(number, ())) for number in facts}
        for number in facts:
            if number in return_facts:
                dependencies[number].update(return_facts[number]['inputs'])
            if number in calls:
                call = calls[number]
                dependencies[number].update([call['function'], *call['args'],
                                             *(value for _, value in call['keywords'])])
            if number in self.operators:
                dependencies[number].update(self.operators[number][2])
            for receiver, _ in attributes.get(number, ()):
                dependencies[number].add(receiver)
            if number in return_slots:
                dependencies[number].update(return_slots[number][1]['return_values'])
            for receiver, selector in reads.get(number, ()):
                dependencies[number].update((receiver, selector))
            dependencies[number].update(iterations.get(number, ()))
        outgoing, conditions = {}, {}
        for number, inputs in dependencies.items():
            for source in inputs:
                outgoing.setdefault(source, set()).add(number)
        for row in guard_records:
            conditions.setdefault(row['node'], set()).update(row['preconditions'])
            self._unknown(row['node'], 'successful_type_guard_bindings_summary_required')
            for source in row['inputs']:
                self._edge(source, row['node'], 'successful_type_guard_control', False)
                outgoing.setdefault(source, set()).add(row['node'])
        for row in local_type_records:
            conditions.setdefault(row['node'], set()).update(row['preconditions'])
            self._unknown(row['node'], 'successful_local_assignment_bindings_summary_required')
            for source in [*row['inputs'], *row['assignment_nodes']]:
                self._edge(source, row['node'], 'successful_local_assignment_control', False)
                outgoing.setdefault(source, set()).add(row['node'])
        for number, record in [*return_facts.items(), *effects.items()]:
            if record.get('preconditions'):
                conditions.setdefault(number, set()).update(record['preconditions'])
        pending = deque(conditions)
        while pending:
            source = pending.popleft()
            for number in outgoing.get(source, ()):
                added = conditions[source] - conditions.get(number, set())
                if added:
                    conditions.setdefault(number, set()).update(added)
                    pending.append(number)

        def conditioned(record, number, inputs=()):
            required = set(record.get('preconditions', ())) | conditions.get(number, set())
            for source in inputs:
                required.update(conditions.get(source, ()))
            return {**record, 'preconditions': sorted(required)} if required else record

        reports = []
        for number, effect in sorted(effects.items()):
            operation = effect['operation']
            if 'effect_obligation' in effect:
                reason = effect['effect_obligation']
            elif number in self.operators:
                reason = 'operand_protocol_summary_required:' + operation
            elif operation.startswith('builtins.'):
                reason = 'external_api_summary_required:' + operation
            elif operation == 'immutable_sequence_subscript':
                reason = 'subscript_receiver_summary_required'
            else:
                reason = 'iteration_receiver_summary_required'
            discharged = reason if (number, reason) in self.unclassified else None
            self.unclassified.discard((number, reason))
            for source in effect['inputs']:
                self._edge(source, number, 'primitive_operation', False)
            reports.append(conditioned({**effect, 'implicit_callbacks': [],
                                        'discharged_obligation': discharged}, number, effect['inputs']))
        for operand, destination in sorted(set(self.truth_tests)):
            value = types(operand)
            if value and value <= truth:
                reports.append(conditioned({'node': destination, 'operation': 'truth_test', 'inputs': [operand],
                                            'output_types': ['bool'], 'implicit_callbacks': []}, destination, [operand]))
                self._edge(operand, destination, 'primitive_truth_control', False)
            else:
                self._unknown(destination, 'truth_value_protocol_summary_required')
        result_types = []
        for number, fact in sorted(return_facts.items()):
            obligation = fact.get('effect_obligation', 'external_api_summary_required:' + fact['callee'])
            result_types.append(conditioned({**fact, 'unresolved_effect_obligation':
                                             obligation if (number, obligation) in self.unclassified else None}, number))
            for source in fact['inputs']:
                self._edge(source, number, 'builtin_return_provenance', False)
        local_returns = []
        for slot, (identity, definition) in sorted(return_slots.items()):
            if slot in facts:
                local_returns.append(conditioned({'function': identity, 'node': definition['node'], 'return_slot': slot,
                                      'inputs': definition['return_values'], 'output_facts': sorted(facts[slot]),
                                      'output_types': sorted(types(slot)), 'condition': 'successful_return'}, slot))
        self.json_decoded_member_inventory = PythonJsonDecodedMembers(self, facts).analyze(result_types)
        argument_records = self._argument_inventory(facts, conditions)
        context_analysis = PythonCallContextTypes(self, facts)
        call_contexts = context_analysis.analyze_bindings(argument_records, conditions)
        call_context_closure = context_analysis.analyze_closure(argument_records, conditions, call_contexts)
        dictionary_comparisons = context_analysis.dictionary_comparisons(call_context_closure, argument_records, conditions)
        return reports, result_types, local_returns, [conditioned(local_call_facts[node], node)
                                                      for node in sorted(local_call_facts)], guard_records, argument_records, [conditioned(row, row['node'], row['inputs']) for row in local_type_records], call_contexts, call_context_closure, dictionary_comparisons

    def _constructor_global_storage(self, references, contained):
        """Expose actual borrowed storage paths for constructor prerequisites.

        These are flow-insensitive observations, not initialization or effect
        acceptance. In particular, an empty write list cannot discharge opaque
        callbacks, module access or mutations outside the modeled graph.
        """
        requested = {}
        for proof in self.closed_constructor_inventory:
            for node in proof['nodes']:
                if node['operation'] == 'global_read':
                    key = node['source']['path'], node['name']
                    requested.setdefault(key, set()).add(proof['id'])
        selected = {}
        for (path, name), proofs in sorted(requested.items()):
            scope = self.modules[Path(path).stem]
            symbol = self.scopes[scope]['symbols'].get(name)
            if symbol is None:
                continue
            roots = {identity for kind, identity, _ in references.get(symbol, ()) if kind == 'container'}
            owned, pending = set(), list(roots)
            while pending:
                identity = pending.pop()
                if identity in owned:
                    continue
                owned.add(identity)
                pending.extend(child for kind, child, _ in references.get(self.members[identity], ())
                               if kind == 'container' and child not in owned)
            selected[path, name] = (symbol, proofs, roots, owned)
        all_owned = set().union(*(row[3] for row in selected.values())) if selected else set()
        aliases = {identity: set() for identity in all_owned}
        for number, values in references.items():
            for kind, identity, _ in values:
                if kind == 'container' and identity in aliases:
                    aliases[identity].add(number)
        storage_owners = {}
        for identity in all_owned:
            storage_owners[self.members[identity]] = identity
            if identity in self.container_updates:
                storage_owners[self.container_updates[identity]] = identity
            if identity in self.container_keys:
                storage_owners[self.container_keys[identity]] = identity
        for (identity, _), number in self.container_slots.items():
            if identity in all_owned:
                storage_owners[number] = identity
        writes, incoming = [], {}
        symbols = {row[0] for row in selected.values()}
        for source, target, kind, reference in sorted(self.edges):
            if target in symbols and reference:
                incoming.setdefault(target, []).append({'node': source, 'kind': kind})
            if kind == 'mutation_control' and target in storage_owners:
                writes.append({'node': source, 'storage_node': target, 'object': storage_owners[target]})
        namespaces = {}
        for path in sorted({path for path, _ in selected}):
            module = Path(path).stem
            namespace_aliases = {number for number, values in references.items()
                       if ('module', module, '') in values}
            attributes = [{'receiver': receiver, 'attribute': attribute, 'node': value, 'write': write}
                          for receiver, attribute, value, write in self.attributes if receiver in namespace_aliases]
            uses = []
            for call in self.calls:
                arguments = []
                for position, keyword, number in [*((i, None, n) for i, n in enumerate(call['args'])),
                                                  *((None, key, n) for key, n in call['keywords'])]:
                    direct = number in namespace_aliases
                    if direct or module in contained(number, 'module'):
                        arguments.append({'position': position, 'keyword': keyword, 'node': number,
                                          'access': 'direct' if direct else 'contained'})
                if not arguments:
                    continue
                targets = sorted(references.get(call['function'], ()))
                local = bool(targets) and all(kind in ('function', 'bound') for kind, _, _ in targets)
                uses.append({'node': call['node'], 'callee_node': call['function'],
                             'targets': [list(value) for value in targets], 'arguments': arguments,
                             'category': 'local_call' if local else 'opaque_namespace_escape'})
            returns = [{'function': identity, 'node': definition['return'],
                        'definition_node': definition['node']}
                       for identity, definition in sorted(self.definitions.items())
                       if definition['kind'] == 'function' and definition['return'] in namespace_aliases]
            relevant = namespace_aliases | {row['node'] for row in attributes + uses}
            namespaces[path] = {'contract': 'python_module_namespace_use.v1', 'module': module,
                                'alias_nodes': sorted(namespace_aliases), 'attribute_uses': attributes,
                                'argument_uses': uses, 'return_sites': returns,
                                'unresolved': [{'node': number, 'reason': reason}
                                               for number, reason in sorted(self.unclassified)
                                               if number in relevant],
                                'status': 'opaque_namespace_escape' if any(
                                    row['category'] == 'opaque_namespace_escape' for row in uses)
                                          else 'no_modeled_namespace_escape',
                                'namespace_effects_accepted': False}
        rows = []
        for (path, name), (symbol, proofs, roots, owned) in sorted(selected.items()):
            def objects(number):
                return sorted(identity for kind, identity, _ in references.get(number, ())
                              if kind == 'container' and identity in owned)
            alias_nodes = set().union(*(aliases[identity] for identity in owned)) if owned else set()
            subscripts = [{'receiver': receiver, 'selector': selector, 'node': value,
                           'write': write, 'objects': objects(receiver)}
                          for receiver, selector, value, write in self.subscripts if objects(receiver)]
            attributes = [{'receiver': receiver, 'attribute': attribute, 'node': value,
                           'write': write, 'objects': objects(receiver)}
                          for receiver, attribute, value, write in self.attributes if objects(receiver)]
            calls = []
            for call in self.calls:
                arguments = [{'position': index, 'keyword': None, 'node': number, 'objects': objects(number)}
                             for index, number in enumerate(call['args']) if objects(number)]
                arguments.extend({'position': None, 'keyword': key, 'node': number, 'objects': objects(number)}
                                 for key, number in call['keywords'] if objects(number))
                targets = sorted(references.get(call['function'], ()))
                receivers = sorted({identity for kind, _, identity in targets
                                    if kind == 'container_method' and identity in owned})
                if not arguments and not receivers:
                    continue
                kinds = {kind for kind, _, _ in targets}
                category = ('local_call' if kinds and kinds <= {'function', 'bound'} else
                            'container_call' if kinds == {'container_method'} else 'opaque_call')
                calls.append({'node': call['node'], 'callee_node': call['function'],
                              'targets': [list(value) for value in targets], 'category': category,
                              'arguments': arguments, 'receiver_objects': receivers})
            returns = [{'function': identity, 'node': definition['return'],
                        'definition_node': definition['node'], 'objects': objects(definition['return'])}
                       for identity, definition in sorted(self.definitions.items())
                       if definition['kind'] == 'function' and objects(definition['return'])]
            mutations = [row for row in writes if row['object'] in owned]
            relevant = alias_nodes | {row['node'] for row in subscripts + attributes + calls + mutations}
            obligations = [{'node': number, 'reason': reason} for number, reason in sorted(self.unclassified)
                           if number in relevant]
            binding_inputs = incoming.get(symbol, [])
            status = ('multiple_binding_inputs' if len(binding_inputs) != 1 else
                      'modeled_storage_write' if mutations or any(row['write'] for row in subscripts + attributes) else
                      'opaque_namespace_escape' if namespaces[path]['status'] == 'opaque_namespace_escape' else
                      'opaque_borrow_escape' if any(row['category'] == 'opaque_call' for row in calls) else
                      'no_modeled_write_or_opaque_borrow_escape')
            rows.append({'contract': 'python_constructor_global_storage.v2', 'path': path, 'name': name,
                         'source_sha256': digest(self.sources[path]), 'constructor_proofs': sorted(proofs),
                         'binding_node': symbol, 'binding_inputs': binding_inputs,
                         'binding_references': [list(value) for value in sorted(references.get(symbol, ()))],
                         'root_objects': sorted(roots),
                         'objects': [{'identity': identity, 'kind': self.container_kinds[identity],
                                      'members_node': self.members[identity],
                                      'alias_nodes': sorted(aliases[identity])} for identity in sorted(owned)],
                         'subscript_uses': subscripts, 'attribute_uses': attributes,
                         'call_uses': calls, 'local_return_sites': returns,
                         'mutation_sources': mutations, 'unresolved': obligations, 'status': status,
                         'module_namespace': namespaces[path],
                         'module_initialization_accepted': False, 'binding_stability_accepted': False,
                         'storage_mutation_closure_accepted': False, 'source_audit_complete': False})
        return rows

    def _function_environment_inventory(self, references, slots, call_receivers):
        """Trace held namespaces/defaults/cells without aliasing their holder.

        Cells use lexical symbol identity and retain every possible binding.
        A nested function can make an intermediate function retain a cell.
        Reachability is not an effect summary for the opaque recipient.
        """
        owners = {number: scope for scope, record in self.scopes.items()
                  for number in record['symbols'].values()}
        owners.update({number: scope for scope, number in self.class_cells.items()})
        functions = {definition['scope']: identity for identity, definition in self.definitions.items()
                     if definition['kind'] == 'function'}
        cells = {scope: set() for scope in functions}
        lookups = set(self.symbol_lookups)
        # An explicit nonlocal declaration retains the cell even if the
        # function neither reads nor writes it in a reachable statement.
        for scope, record in self.scopes.items():
            for name in record['nonlocals']:
                parent = record['parent']
                while parent is not None:
                    outer = self.scopes[parent]
                    if outer['kind'] != 'class' and name in outer['locals']:
                        if name in outer['symbols']:
                            lookups.add((scope, outer['symbols'][name]))
                        break
                    parent = outer['parent']
        for scope, symbol in sorted(lookups):
            owner = owners.get(symbol)
            if owner is None or (self.scopes[owner]['kind'] not in ('function', 'comprehension')
                                 and symbol not in self.class_cells.values()):
                continue
            cursor, crossed = scope, []
            while cursor is not None and cursor != owner:
                crossed.append(cursor)
                cursor = self.scopes[cursor]['parent']
            if cursor == owner:
                for item in crossed:
                    if item in cells:
                        cells[item].add(symbol)
        modules = [{'module': module, 'path': scope[0], 'scope': list(scope),
                    'symbols': [{'name': name, 'node': number}
                                for name, number in sorted(self.scopes[scope]['symbols'].items())]}
                   for module, scope in sorted(self.modules.items())]
        globals_by_module = {row['module']: [item['node'] for item in row['symbols']] for row in modules}
        annotation_values = {}
        for source, target, kind, _ in self.edges:
            if kind == 'annotation_evaluation':
                annotation_values.setdefault(target, set()).add(source)
        annotations_by_owner = {}
        for row in self.annotation_inventory:
            if row['storage'] == 'function':
                annotations_by_owner.setdefault(row['owner'], []).append(row)
        rows, environments = [], {}
        for scope, identity in sorted(functions.items()):
            definition = self.definitions[identity]
            module = Path(scope[0]).stem
            defaults = [{'parameter': name, 'node': number}
                        for name, number in sorted(definition['default_values'].items())]
            captured = [{'name': self.nodes[number]['label'], 'symbol': number,
                         'owner_scope': list(owners[number])} for number in sorted(cells[scope])]
            annotations = [{**row, 'value_nodes': sorted(annotation_values.get(row['node'], ()))}
                           for row in annotations_by_owner.get(definition['node'], ())]
            capture_nodes = sorted({*(row['node'] for row in defaults), *cells[scope],
                                    *(number for row in annotations for number in row['value_nodes'])})
            environments[identity] = {'module': module, 'capture_nodes': capture_nodes,
                                      'global_nodes': globals_by_module[module]}
            rows.append({'function': identity, 'node': definition['node'], 'scope': list(scope),
                         'module': module, 'defaults': defaults, 'closure_cells': captured,
                         'annotations': annotations, 'capture_nodes': capture_nodes})
        receiver_roots = call_receivers['receiver_roots']
        contained = self._contained_objects(references, slots, extra_roots=receiver_roots,
                                            function_environments=environments)
        arguments = []
        for call in self.calls:
            targets = sorted(references.get(call['function'], ()))
            if targets and all(kind in ('function', 'bound') for kind, _, _ in targets):
                continue
            for position, keyword, number in [*((i, None, n) for i, n in enumerate(call['args'])),
                                              *((None, key, n) for key, n in call['keywords'])]:
                arguments.append({'call_node': call['node'], 'callee_node': call['function'],
                                  'targets': [list(value) for value in targets], 'position': position,
                                  'keyword': keyword, 'node': number,
                                  'function_namespaces': sorted(contained(number, 'namespace')),
                                  'module_objects': sorted(contained(number, 'module'))})
        return {'contract': 'python_function_environment_capture.v1', 'modules': modules,
                'functions': rows, 'opaque_arguments': arguments,
                'opaque_receivers': [{'node': number,
                                      'function_namespaces': sorted(contained(number, 'namespace')),
                                      'module_objects': sorted(contained(number, 'module'))}
                                     for number in receiver_roots],
                'scope': 'modeled_function_globals_defaults_lexical_cells_and_annotation_values',
                'binding_model': 'flow_insensitive_possible_bindings',
                'namespace_capability_is_module_alias': False,
                'implicit_class_cell_semantics_accepted': False,
                'class_object_capture_semantics_accepted': False,
                'annotation_runtime_semantics_accepted': False,
                'function_environment_semantics_accepted': False,
                'native_recipient_effects_accepted': False, 'source_audit_complete': False}

    def _constructor_callable_bindings(self, references, slots):
        """Inventory function objects required by the closed constructors.

        Module binding, callable attribute state and argument escape are
        separate dependencies. An invocation is not an argument escape, and
        an empty modeled write set is not a callable-body stability proof.
        Function globals/default/closure capture remains explicitly unproved.
        """
        requested = {}
        for proof in self.closed_constructor_inventory:
            path = proof['function'].split('::', 1)[0]
            for node in proof['nodes']:
                if node['operation'] == 'function_return':
                    requested.setdefault((path, node['function']), set()).add(proof['id'])
        if not requested:
            return []
        selected = {}
        for (path, name), proofs in sorted(requested.items()):
            scope = self.modules[Path(path).stem]
            symbol = self.scopes[scope]['symbols'].get(name)
            definitions = [identity for identity, definition in self.definitions.items()
                           if definition['kind'] == 'function'
                           and self.scopes[definition['scope']]['parent'] == scope
                           and self.scopes[definition['scope']]['name'] == name]
            # A source trace identifies a declaration, not whichever function
            # a later assignment happens to install under the same name.
            selected[path, name] = (symbol, proofs, definitions)
        identities = {identity for _, _, definitions in selected.values() for identity in definitions}
        roots = {number for call in self.calls
                 for number in [*call['args'], *(n for _, n in call['keywords'])]}
        roots.update(definition['return'] for definition in self.definitions.values()
                     if definition['kind'] == 'function')
        contained = self._contained_objects(references, slots, extra_roots=roots,
                                            terminal_functions=identities)
        aliases = {identity: set() for identity in identities}
        for number, values in references.items():
            for kind, identity, _ in values:
                if kind in ('function', 'bound') and identity in aliases:
                    aliases[identity].add(number)
        incoming = {}
        symbols = {symbol for symbol, _, _ in selected.values() if symbol is not None}
        for source, target, kind, reference in sorted(self.edges):
            if target in symbols and reference:
                incoming.setdefault(target, []).append({'node': source, 'kind': kind})
        rows = []
        for (path, name), (symbol, proofs, definitions) in sorted(selected.items()):
            owned = set(definitions)
            alias_nodes = set().union(*(aliases[identity] for identity in owned)) if owned else set()
            attributes = [{'receiver': receiver, 'attribute': attribute, 'node': value, 'write': write}
                          for receiver, attribute, value, write in self.attributes if receiver in alias_nodes]
            invocations, uses = [], []
            for call in self.calls:
                targets = sorted(references.get(call['function'], ()))
                if call['function'] in alias_nodes:
                    invocations.append({'node': call['node'], 'callee_node': call['function'],
                                        'targets': [list(target) for target in targets]})
                arguments = []
                for position, keyword, number in [*((i, None, n) for i, n in enumerate(call['args'])),
                                                  *((None, key, n) for key, n in call['keywords'])]:
                    direct = number in alias_nodes
                    if direct or owned.intersection(contained(number, 'function')):
                        arguments.append({'position': position, 'keyword': keyword, 'node': number,
                                          'access': 'direct' if direct else 'contained'})
                if arguments:
                    local = bool(targets) and all(kind in ('function', 'bound') for kind, _, _ in targets)
                    uses.append({'node': call['node'], 'callee_node': call['function'],
                                 'targets': [list(target) for target in targets], 'arguments': arguments,
                                 'category': 'local_call' if local else 'opaque_callable_escape'})
            returns = [{'function': identity, 'node': definition['return'],
                        'definition_node': definition['node'],
                        'access': 'direct' if definition['return'] in alias_nodes else 'contained'}
                       for identity, definition in sorted(self.definitions.items())
                       if definition['kind'] == 'function' and
                       (definition['return'] in alias_nodes or
                        owned.intersection(contained(definition['return'], 'function')))]
            binding_inputs = incoming.get(symbol, [])
            relevant = alias_nodes | {row['node'] for row in attributes + invocations + uses + returns}
            unresolved = [{'node': number, 'reason': reason} for number, reason in sorted(self.unclassified)
                          if number in relevant]
            status = ('declaration_unresolved' if symbol is None or len(definitions) != 1 else
                      'multiple_binding_inputs' if len(binding_inputs) != 1 else
                      'modeled_callable_attribute_write' if any(row['write'] for row in attributes) else
                      'opaque_callable_escape' if any(row['category'] == 'opaque_callable_escape' for row in uses) else
                      'no_modeled_callable_write_or_escape')
            rows.append({'contract': 'python_constructor_callable_binding.v1', 'path': path, 'name': name,
                         'source_sha256': digest(self.sources[path]), 'constructor_proofs': sorted(proofs),
                         'binding_node': symbol, 'binding_inputs': binding_inputs,
                         'binding_references': [list(value) for value in sorted(references.get(symbol, ()))],
                         'declarations': [{'identity': identity, 'node': self.definitions[identity]['node']}
                                          for identity in sorted(definitions)],
                         'alias_nodes': sorted(alias_nodes), 'attribute_uses': attributes,
                         'invocations': invocations, 'argument_uses': uses, 'return_sites': returns,
                         'unresolved': unresolved, 'status': status,
                         'binding_stability_accepted': False, 'callable_body_stability_accepted': False,
                         'function_capture_semantics_accepted': False, 'native_callback_effects_accepted': False,
                         'source_audit_complete': False})
        return rows

    def _class_mro(self, identity, references, active=()):
        """C3 over uniquely resolved declared bases; native ancestry stays open.

        This is a conditional lookup order, not proof of stable bases,
        metaclass execution, descriptors or the runtime receiver's exact type.
        """
        if identity in active:
            return None
        definition = self.definitions[identity]
        bases = []
        for number in definition['bases']:
            values = references.get(number, ())
            if len(values) != 1:
                return None
            kind, name, _ = next(iter(values))
            if kind not in ('class', 'external'):
                return None
            bases.append((kind, name))
        if not bases:
            bases = [('external', 'builtins.object')]
        sequences = []
        for kind, name in bases:
            order = self._class_mro(name, references, (*active, identity)) if kind == 'class' else [(kind, name)]
            if order is None:
                return None
            sequences.append(list(order))
        sequences.append(list(bases))
        result = [('class', identity)]
        while any(sequences):
            sequences = [row for row in sequences if row]
            candidate = next((row[0] for row in sequences
                              if all(row[0] not in other[1:] for other in sequences)), None)
            if candidate is None:
                return None
            result.append(candidate)
            for row in sequences:
                if row[0] == candidate:
                    row.pop(0)
        return result

    def _class_candidates(self, identity, references):
        pending, seen = [('class', identity)], set()
        while pending:
            kind, name = pending.pop()
            if (kind, name) in seen:
                continue
            seen.add((kind, name))
            if kind == 'class':
                for base in self.definitions[name]['bases']:
                    pending.extend((k, n) for k, n, _ in references.get(base, ()) if k in ('class', 'external'))
        return sorted(seen)

    def _super_call(self, call, references):
        self._unknown(call['node'], 'super_native_dispatch_and_retention_effects_required')
        if call['starred'] or call['keywords']:
            return
        if len(call['args']) == 2:
            start, receiver = call['args']
        elif not call['args']:
            scope = call.get('lexical_scope')
            record = self.scopes.get(scope)
            if record is None or record['kind'] != 'function' or '__class__' not in record['compiler_frees']:
                self._unknown(call['node'], 'super_implicit_context_missing')
                return
            syntax = record['tree']
            positional = [*syntax.args.posonlyargs, *syntax.args.args]
            if not positional:
                self._unknown(call['node'], 'super_first_argument_missing')
                return
            start = self._symbol('__class__', scope)
            receiver = self._symbol(positional[0].arg, scope)
        else:
            self._unknown(call['node'], 'super_argument_shape_unresolved')
            return
        self.super_inputs[call['node']] = {'call_node': call['node'], 'class_node': start,
                                         'receiver_node': receiver, 'implicit': not call['args']}
        self._edge(start, call['node'], 'super_start_class', False)
        self._edge(receiver, call['node'], 'super_receiver', False)
        for kind, identity, _ in references.get(start, ()):
            if kind == 'class':
                self._seed(call['node'], 'super_proxy', identity, str(receiver))

    def _class_attribute(self, receiver, kind, identity, attribute, value, write,
                         references, slots, after=None):
        if write and after is not None:
            self._unknown(value, 'super_attribute_write_effects_required')
            return
        order = self._class_mro(identity, references)
        ordered = order is not None
        if order is None:
            order = self._class_candidates(identity, references)
            self._unknown(value, 'class_mro_unresolved')
            if after is not None:
                order = [row for row in order if row != ('class', after)]
        elif after is not None:
            if ('class', after) not in order:
                self._unknown(value, 'super_receiver_subtype_unresolved')
                return
            order = order[order.index(('class', after)) + 1:]
        if write:
            order = [('class', identity)]
        self.class_dispatches[receiver, kind, identity, attribute, value, write, after or ''] = {
            'receiver_node': receiver, 'receiver_kind': kind, 'receiver_class': identity,
            'attribute': attribute, 'value_node': value, 'write': write, 'after_class': after,
            'candidate_owners': [list(row) for row in order],
            'dispatch_semantics_accepted': False}
        for owner_kind, owner in order:
            if owner_kind == 'external':
                if not write and (owner != 'builtins.object' or after is not None):
                    self._seed(value, 'external', owner + '.' + attribute)
                    self._unknown(value, 'native_base_attribute_effects_required:' + owner)
                continue
            definition = self.definitions[owner]
            self._edge(definition['node'], value, 'class_attribute_basis', False)
            slot = owner, attribute
            if slot not in slots:
                slots[slot] = self._derived_node('attribute_slot', owner + '.' + attribute, definition['node'])
            storage = slots[slot]
            if write:
                self._edge(value, storage, 'field_write')
                continue
            self._edge(storage, value, 'field_read')
            symbol = self.scopes[definition['scope']]['symbols'].get(attribute)
            if symbol is None:
                continue
            for member_kind, member_identity, member_receiver in sorted(references.get(symbol, ())):
                if member_kind == 'function':
                    member = self.definitions[member_identity]
                    if member['property']:
                        self._edge(member['return'], value, 'property_return')
                        self._edge(receiver, member['activation'], 'property_dispatch', False)
                        self._unknown(value, 'property_descriptor_summary_required')
                    elif kind == 'class' or member['staticmethod']:
                        self._seed(value, 'function', member_identity)
                    else:
                        self._seed(value, 'bound', member_identity, identity)
                else:
                    self._seed(value, member_kind, member_identity, member_receiver)
            # This declared slot is first in the conditional C3 lookup.
            # Native descriptor/binding effects remain an explicit obligation.
            if ordered and references.get(symbol):
                break
        self._edge(receiver, value, 'receiver', False)
        if after is not None or len(order) > 1:
            self._unknown(value, 'class_mro_descriptor_and_binding_effects_required')

    def build(self):
        # Attribute slots are qualified by the defining class. This prevents
        # an unrelated object's same-spelled field from acquiring its aliases.
        # Reference sets contain possible targets, not runtime execution order.
        # Visit them canonically before allocating nodes or selecting a first
        # source origin. Process hash randomization must not change evidence.
        slots, external_slots, linked, call_targets = {}, {}, set(), {}
        receiver_attributes = set()
        members = self.members
        for iteration in range(128):
            before = len(self.edges), sum(len(value) for value in self.seeds.values())
            references = self._references()
            for receiver, attribute, value, write in self.attributes:
                for kind, identity, receiver_identity in sorted(references.get(receiver, ())):
                    if kind in ('path_object', 'stream_object', 'json_value'):
                        token = (kind, identity, receiver, attribute, value, write)
                        if token in receiver_attributes:
                            continue
                        receiver_attributes.add(token)
                    if kind in ('instance', 'class'):
                        self._class_attribute(receiver, kind, identity, attribute, value, write, references, slots)
                    elif kind == 'super_proxy':
                        retained = int(receiver_identity)
                        for receiver_kind, receiver_class, _receiver in sorted(references.get(retained, ())):
                            if receiver_kind in ('instance', 'class'):
                                self._class_attribute(retained, receiver_kind, receiver_class, attribute, value,
                                                      write, references, slots, after=identity)
                        self._edge(receiver, value, 'super_attribute_dispatch', False)
                    elif kind == 'module':
                        # Attribute stores share the module's actual namespace
                        # with global reads and from-import aliases. Keep all
                        # possible values; this graph does not prove store order.
                        storage = self._symbol(attribute, self.modules[identity], True)
                        if write:
                            self._edge(value, storage, 'module_attribute_write')
                            self._edge(receiver, value, 'module_attribute_write_receiver', False)
                            self._unknown(value, 'module_attribute_write_summary_required:' + attribute)
                        else:
                            self._edge(storage, value, 'module_attribute')
                    elif kind == 'external':
                        # An imported module is mutable storage. Connect its
                        # actual member writes to reads through every alias.
                        # Retain the original external target as a possible
                        # value: this graph does not establish write order.
                        slot = (identity, attribute)
                        api = identity + '.' + attribute
                        if slot not in external_slots:
                            external_slots[slot] = self._derived_node('external_attribute_slot', api, receiver)
                        storage = external_slots[slot]
                        self._edge(receiver, storage, 'external_attribute_receiver', False)
                        if write:
                            self._edge(value, storage, 'external_attribute_write')
                            self._unknown(value, 'external_attribute_write_summary_required:' + attribute)
                        else:
                            self._seed(value, 'external', api)
                            self._edge(storage, value, 'external_attribute_read')
                            self._edge(receiver, value, 'external_attribute', False)
                            if api in ('sys.stdin', 'sys.stdout', 'sys.stderr', 'sys.__stdin__', 'sys.__stdout__', 'sys.__stderr__'):
                                stream = self._stream_object(value, 'external', api, [receiver])
                                self._stream_operation(value, api, stream, [receiver], ('platform_input',))
                    elif kind == 'hash_object':
                        if not write and attribute in ('update', 'digest', 'hexdigest', 'copy'):
                            self._seed(value, 'hash_method', attribute, identity)
                            self._edge(receiver, value, 'hash_receiver', False)
                        else:
                            self._edge(self.hash_states[identity], value, 'hash_attribute_input', False)
                            self._unknown(value, 'hash_attribute_summary_required:' + attribute)
                    elif kind == 'path_object':
                        self._path_attribute(receiver, identity, attribute, value, write)
                    elif kind == 'stream_object':
                        self._stream_attribute(receiver, identity, attribute, value, write)
                    elif kind == 'json_value':
                        self._json_attribute(receiver, identity, attribute, value, write)
                    elif kind in ('path_parents', 'path_iterator'):
                        self._edge(self.path_states[identity], value, 'path_attribute_input', False)
                        if write:
                            self._edge(value, self.path_states[identity], 'path_attribute_mutation', False)
                        self._unknown(value, 'path_sequence_attribute_summary_required:' + attribute)
                    elif kind == 'container' and not write:
                        methods = {
                            'dict': {'get', 'setdefault', 'pop', 'update', 'keys', 'values', 'items',
                                     'copy', 'clear', '__getitem__', '__setitem__'},
                            'list': {'append', 'extend', 'insert', 'pop', 'copy', 'clear', 'reverse',
                                     '__getitem__', '__setitem__'},
                            'tuple': {'__getitem__'},
                            'set': {'add', 'update', 'pop', 'copy', 'clear'}}
                        if attribute in methods.get(self.container_kinds[identity], set()):
                            self._seed(value, 'container_method', attribute, identity)
                            self._edge(receiver, value, 'container_receiver', False)
                        else:
                            self._unknown(value, 'container_attribute_summary_required:' + attribute)
                    elif kind == 'container' and write:
                        self._unknown(value, 'builtin_container_attribute_write')
            for receiver, selector, value, write in self.subscripts:
                for kind, identity, _ in sorted(references.get(receiver, ())):
                    if kind == 'container':
                        if write:
                            self._container_write(identity, selector, value, value)
                        else:
                            self._container_read(identity, selector, value)
                    elif kind == 'path_parents':
                        self._edge(self.path_states[identity], value, 'path_parent_input', False)
                        # Slices return tuples; arbitrary __index__ callbacks
                        # and successful-result shapes remain unresolved.
                        if not write and type(self.literals.get(selector)) is int:
                            self._path_operation(value, 'pathlib._PathParents.__getitem__',
                                                 [receiver, selector, self.path_states[identity]], 'path_object')
                        else:
                            if write:
                                self._edge(value, self.path_states[identity], 'path_attribute_mutation', False)
                            self._unknown(value, 'path_parent_selector_summary_required')
                self._edge(receiver, value, 'subscript_receiver', False)
                self._edge(selector, value, 'subscript_selector', False)
            for receiver, value in self.iterations:
                for kind, identity, _ in sorted(references.get(receiver, ())):
                    if kind == 'container':
                        source = self.container_keys.get(identity, members[identity])
                        self._edge(source, value, 'iteration_value')
                    elif kind in ('path_iterator', 'path_parents'):
                        self._path_operation(value, 'pathlib.' + kind + '.__next__',
                                             [receiver, self.path_states[identity]], 'path_object',
                                             ('filesystem_read', 'platform_input') if kind == 'path_iterator' else ())
                        self._unknown(value, 'path_iteration_lifecycle_summary_required')
                self._edge(receiver, value, 'iteration_control', False)
            for node, (family, operations, operands) in sorted(self.operators.items()):
                if family != 'BinOp' or operations != ['Div']:
                    continue
                for index, receiver in enumerate(operands):
                    for kind, identity, _ in sorted(references.get(receiver, ())):
                        if kind == 'path_object':
                            api = 'pathlib.Path.' + ('__truediv__' if index == 0 else '__rtruediv__')
                            self._path_operation(node, api, [*operands, self.path_states[identity]], 'path_object')
                            self._unknown(node, 'path_operand_dispatch_summary_required')
            for receiver, destination, control, _ in sorted(self.container_transfers):
                for kind, identity, _ in sorted(references.get(receiver, ())):
                    if kind == 'container' and self.container_kinds[identity] == 'dict':
                        self._container_write(destination, None, members[identity], control)
                        self._edge(self.container_keys[identity], self.container_keys[destination], 'mapping_update_keys')
                    elif kind == 'container':
                        token = receiver, destination, control, identity
                        if token not in self.mapping_pair_reads:
                            self.mapping_pair_reads.add(token)
                            projected = []
                            for index in (0, 1):
                                selector = self._derived_node('constant_index', str(index), control)
                                self.literals[selector] = index
                                item = self._derived_node('mapping_pair_item', str(index), control)
                                self.subscripts.append((members[identity], selector, item, False))
                                projected.append(item)
                            self._container_write(destination, projected[0], projected[1], control)
                            self._unknown(control, 'mapping_pair_shape_summary_required')
                    else:
                        self._unknown(control, 'mapping_update_source_summary_required')
            for call in self.calls:
                for kind, identity, receiver in sorted(references.get(call['function'], ())):
                    token = (call['node'], kind, identity, receiver)
                    if token in linked:
                        continue
                    linked.add(token)
                    call_targets.setdefault(call['node'], set()).add((kind, identity, receiver))
                    if kind in ('function', 'bound'):
                        bound = None
                        if kind == 'bound':
                            bound = self._derived_node('bound_receiver', receiver, call['node'])
                            self._seed(bound, 'instance', receiver)
                        self._bind(call, identity, bound)
                    elif kind == 'class':
                        self._seed(call['node'], 'instance', identity)
                        linked.remove(token)
                        order = self._class_mro(identity, references)
                        ordered = order is not None
                        if order is None:
                            order = self._class_candidates(identity, references)
                            self._unknown(call['node'], 'constructor_mro_unresolved')
                        for owner_kind, owner in order:
                            if owner_kind != 'class':
                                self._unknown(call['node'], 'native_constructor_effects_required:' + owner)
                                continue
                            class_scope = self.definitions[owner]['scope']
                            constructor = self.scopes[class_scope]['symbols'].get('__init__')
                            if constructor is None:
                                continue
                            values = references.get(constructor, ())
                            for init_kind, init_identity, _ in sorted(values):
                                if init_kind == 'function':
                                    self._bind(call, init_identity, call['node'], return_value=False)
                            if ordered and values:
                                break
                    elif kind == 'external':
                        if identity == 'builtins.super':
                            self._super_call(call, references)
                            linked.remove(token)
                        self._unknown(call['node'], 'external_api_summary_required:' + identity)
                        if identity in ('hashlib.sha256', 'hashlib.sha1'):
                            hashed = self._hash_object(call['node'], identity.split('.')[-1])
                            self._edge(call['node'], self.hash_states[hashed], 'hash_initialization', False)
                            self._unknown(call['node'], 'stdlib_binding_summary_required:hashlib')
                        elif identity != 'builtins.super' and not self._reflective_attribute_call(call, identity) and not self._path_call(call, identity) and not self._stream_factory(call, identity) and not self._json_call(call, identity) and not self._builtin_container(call, identity):
                            self._seed(call['node'], 'external_result', identity)
                        self._builtin_callbacks(call, identity)
                        self._edge(call['function'], call['node'], 'external_call', False)
                        for argument in [*call['args'], *(value for _, value in call['keywords'])]:
                            self._edge(argument, call['node'], 'external_argument', False)
                    elif kind == 'container_method':
                        self._container_method(call, identity, receiver)
                    elif kind == 'hash_method':
                        self._hash_method(call, identity, receiver)
                    elif kind == 'path_method':
                        self._path_call(call, identity, int(receiver))
                    elif kind == 'stream_method':
                        self._stream_method(call, identity, receiver)
                    elif kind == 'json_method':
                        self._json_method(call, identity, receiver)
                    else:
                        self._unknown(call['node'], 'callable_identity_unclassified:' + kind)
            self._sequence_protocols(references)
            self._dictionary_protocols()
            self._sorted_protocols(references)
            self._link_builtin_protocols(references)
            contained = self._contained_objects(references, slots)
            self._hash_escapes(references, slots, contained)
            self._path_escapes(references, slots, contained)
            self._stream_protocols(references)
            self._stream_escapes(references, slots, contained)
            self._json_protocols(references, slots, contained)
            after = len(self.edges), sum(len(value) for value in self.seeds.values())
            if before == after:
                break
        else:
            raise ValueError('lcer.source_graph_did_not_converge')
        references = self._references()
        self._annotation_consumers(references)
        for receiver, attribute, value, _ in self.attributes:
            values = references.get(receiver, ())
            if not values or any(kind not in ('class', 'instance', 'module', 'external', 'container', 'hash_object') for kind, _, _ in values):
                self._unknown(value, 'attribute_receiver_summary_required:' + attribute)
        for receiver, _, value, _ in self.subscripts:
            # A known container alias alone does not prove selector hooks,
            # complete receiver identity, or replacement/finalizer effects.
            self._unknown(value, 'subscript_receiver_summary_required')
        for receiver, value in self.iterations:
            self._unknown(value, 'iteration_receiver_summary_required')
        for receiver, _, value, _ in sorted(self.container_transfers):
            if not references.get(receiver):
                self._unknown(value, 'mapping_update_source_summary_required')
        for call in self.calls:
            if not call_targets.get(call['node']):
                self._unknown(call['node'], 'call_target_unresolved')
        primitive_effects, builtin_return_facts, function_return_facts, local_call_return_facts, guard_records, argument_records, local_type_records, call_contexts, call_context_closure, dictionary_comparisons = self._primitive_effects()
        constructor_references = self._references()
        constructor_containment = self._contained_objects(constructor_references, slots, record=True)
        constructor_storage = self._constructor_global_storage(
            constructor_references, constructor_containment)
        constructor_callables = self._constructor_callable_bindings(constructor_references, slots)
        call_receivers = self._call_receiver_inventory(constructor_references, slots)
        function_environments = self._function_environment_inventory(constructor_references, slots, call_receivers)
        initialization = PythonModuleInitialization(self.sources)
        initialization_records = [initialization.analyze(path)
                                  for path in sorted({row['path'] for row in constructor_storage})]
        initializations_by_path = {row['path']: row for row in initialization_records}
        constructor_initialization = PythonConstructorInitialization(self.sources)
        constructor_initialization_records = [constructor_initialization.bind(
            row, initializations_by_path.get(row['function'].split('::', 1)[0]))
            for row in self.closed_constructor_inventory]
        value_stability = PythonConstructorValueStability(self.sources)
        value_stability_records = [value_stability.analyze(
            row, initializations_by_path.get(row['function'].split('::', 1)[0]), binding)
            for row, binding in zip(self.closed_constructor_inventory, constructor_initialization_records)]
        dictionary_comparisons = PythonConstructorComparisonDependencies(self.sources).bind(
            dictionary_comparisons, self.closed_constructor_inventory, initialization_records,
            constructor_initialization_records, value_stability_records)
        return {'files': [{'path': path, 'sha256': digest(raw), 'size_bytes': len(raw)}
                          for path, raw in sorted(self.sources.items())],
                'nodes': self.nodes,
                'edges': [{'source': source, 'target': target, 'kind': kind, 'reference': identity}
                          for source, target, kind, identity in sorted(self.edges)],
                'calls': [{'node': call['node'], 'callee_node': call['function'],
                           'targets': [list(value) for value in sorted(call_targets.get(call['node'], ()))]}
                          for call in self.calls],
                'unclassified': [{'node': node, 'reason': reason} for node, reason in sorted(self.unclassified)],
                'primitive_effects': primitive_effects,
                'successful_type_guard_inventory': guard_records,
                'builtin_return_facts': builtin_return_facts,
                'builtin_protocol_edges': self.builtin_protocol_edges,
                'sorted_protocol_inventory': self.sorted_protocol_inventory,
                'annotation_inventory': self.annotation_inventory,
                'implicit_class_cell_inventory': [
                    {'scope': list(scope), 'node': number, 'class_identity': next(
                        identity for identity, definition in self.definitions.items() if definition['scope'] == scope),
                     'publication_effects_accepted': False}
                    for scope, number in sorted(self.class_cells.items())],
                'class_dispatch_inventory': [row for _, row in sorted(self.class_dispatches.items())],
                'super_input_inventory': [row for _, row in sorted(self.super_inputs.items())],
                'reflective_attribute_inventory': [row for _, row in sorted(self.reflective_attribute_calls.items())],
                'context_inventory': self.context_inventory,
                'hash_state_inventory': [{'identity': identity, 'algorithm': self.hash_kinds[identity], 'node': node,
                                          'preconditions': ['authentic_stdlib_binding:hashlib'],
                                          'snapshot_model': 'flow_insensitive_possible_inputs'}
                                         for identity, node in sorted(self.hash_states.items())],
                'path_contract_inventory': [{**row, 'inputs': sorted(row['inputs']),
                                             'effects': dict(sorted(row['effects'].items()))}
                                            for _, row in sorted(self.path_operations.items())],
                'stream_state_inventory': [{'identity': identity, 'state_node': state,
                                            **self.stream_metadata[identity]}
                                           for identity, state in sorted(self.stream_states.items())],
                'stream_contract_inventory': [{**row, 'inputs': sorted(row['inputs']),
                                               'effects': dict(sorted(row['effects'].items()))}
                                              for _, row in sorted(self.stream_operations.items())],
                'json_value_inventory': [{'identity': identity, **row} for identity, row in sorted(self.json_values.items())],
                'json_contract_inventory': [{**row, 'inputs': sorted(row['inputs'])}
                                            for _, row in sorted(self.json_operations.items())],
                'json_callback_inventory': self.json_callbacks,
                'json_decoded_member_inventory': self.json_decoded_member_inventory,
                'function_return_inventory': [{'function': identity, 'node': definition['node'],
                                               'return_slot': definition['return'], 'inputs': definition['return_values'],
                                               **definition['return_inventory']}
                                              for identity, definition in sorted(self.definitions.items())
                                              if definition['kind'] == 'function'],
                'function_return_facts': function_return_facts,
                'local_call_return_facts': local_call_return_facts,
                'call_argument_binding_inventory': argument_records,
                'successful_local_type_inventory': local_type_records,
                'call_context_type_inventory': call_contexts,
                'call_context_closure': call_context_closure,
                'context_dictionary_comparison_inventory': dictionary_comparisons,
                'closed_constructor_inventory': self.closed_constructor_inventory,
                'constructor_global_storage_inventory': constructor_storage,
                'constructor_callable_binding_inventory': constructor_callables,
                'function_environment_inventory': function_environments,
                'module_initialization_inventory': initialization_records,
                'constructor_initialization_inventory': constructor_initialization_records,
                'constructor_value_stability_inventory': value_stability_records,
                'object_containment_inventory': constructor_containment.inventory,
                'call_receiver_inventory': call_receivers,
                'source_audit_complete': False}


def authenticated_imports(release_root, artifact_root):
    """Guard the direct import path as well as the eventual normal verifier."""
    context = authenticate_release(release_root, artifact_root)
    root = context["root"]
    standard = set(sys.builtin_module_names)
    library = Path(sysconfig.get_path("stdlib"))
    standard.update(path.stem for path in library.glob("*.py"))
    standard.update(path.name for path in library.iterdir() if path.is_dir() and (path / "__init__.py").is_file())
    extensions = Path(sysconfig.get_config_var("DESTSHARED") or library / "lib-dynload")
    if extensions.is_dir():
        standard.update(path.name.split(".")[0] for path in extensions.iterdir()
                        if path.is_file() and path.suffix in {".so", ".dylib"})
    # -B suppresses bytecode writes, but imports may still read an existing
    # cache. A package directory also takes precedence over a same-name .py.
    # Refuse these undeclared executable substitutes before any local import.
    sys.dont_write_bytecode = True
    sys.pycache_prefix = None
    for path in (root / 'proof_kernel').rglob('*'):
        require(not path.is_symlink())
        require(not (path.is_file() and path.suffix in ('.pyc', '.pyo', '.so', '.dylib')))
        if path.parent == root / 'proof_kernel':
            require(not (path.stem in standard and path.suffix == '.py')
                    and not (path.is_dir() and path.name in standard | LOCAL_MODULES))
    python_dependency_inventory(context['source_bytes'], standard)
    for name in LOCAL_MODULES:
        relative = "proof_kernel/" + name + ".py"
        require(relative in context["source_bytes"])
        loaded = sys.modules.get(name)
        if loaded is not None:
            require(Path(loaded.__file__).absolute() == root / relative)
    for relative, original in context["source_bytes"].items():
        require(ordinary_file(root, relative) == original)
    sys.path[:] = [str(root / "proof_kernel"), *STDLIB_PATHS]
    import concurrent_external_evidence_arbitration as canonical
    import kernel
    # Candidate source bytes belong to the release graph, but a candidate's
    # own manifest cannot authorize its import-time behavior. Independent
    # verification executes only these two immutable predecessor modules.
    for name, module in [("concurrent_external_evidence_arbitration", canonical), ("kernel", kernel)]:
        require(Path(module.__file__).absolute() == root / "proof_kernel" / (name + ".py"))
    return context, canonical


def _base64(value):
    try:
        raw = base64.b64decode(value, validate=True)
        require(base64.b64encode(raw).decode("ascii") == value, "lcer.schema_invalid")
        return raw
    except (ValueError, UnicodeError) as error:
        raise ValueError("lcer.schema_invalid") from error


def _canonical_operations(policy, case_id):
    """Derive call order from the frozen schedule, independently of the harness."""
    require(case_id in policy["artifact_hash_graph"]["case_ids"])
    witnesses = {row["id"]: row for row in policy["witnesses"]}
    programs = {row["id"]: row for row in policy["failure_programs"]}
    prefix = "P5" if case_id in witnesses else programs[case_id]["prefix"] if case_id in programs else "P2"
    operations = []

    def expand(key):
        for value in policy["operation_schedule"]["prefixes"][key]:
            if value in policy["operation_schedule"]["prefixes"]:
                expand(value)
            elif value == "admit QA on R0":
                operations.append(("admit_external_input_candidate", "domain_A"))
            elif value == "admit QB on R0":
                operations.append(("admit_external_input_candidate", "domain_B"))
            elif value == "construct primary fixture batch":
                operations.append(("construct_bext_from_sealed_fixture_set", None))
            elif value == "resolve once and publish exact R1":
                operations.append(("resolve_external_batch", None))

    expand(prefix)
    admission, construction, resolution = tuple(policy["call_trace_contract"]["dispatch"])
    if case_id in witnesses:
        operations[:2] = [(admission, domain) for domain in witnesses[case_id]["presentation"]]
    if case_id.startswith("C"):
        operations.append((resolution, None))
    if case_id == "F01":
        operations.extend([(admission, "domain_A"), (construction, None)])
    if case_id in {"F02", "F03", "F05", "F06"}:
        operations.append((admission, "domain_A"))
    if case_id in {"F04a", "F04b"}:
        operations.extend([(admission, "domain_A"), (admission, "domain_B"), (construction, None)])
    if case_id in {"F10a", "F10b"}:
        operations.append((admission, "domain_A"))
    return operations


def _replay_canonical(policy, artifacts, case, canonical):
    """Check typed raw arguments and repeat actual predecessor calls.

    This is an internal calculation. Release and live-process acceptance also
    require authenticated bytes, transport, source, process and world predicates.
    """
    name = case["witness_id"]
    operations = _canonical_operations(policy, name)
    calls = [row["payload"] for row in case["command_trace"] if row["event_id"] == "canonical_call"]
    require([row["function"] for row in calls] == [function for function, _ in operations])
    r0, r1 = artifacts["canonical/R0.json"], artifacts["canonical/R1.json"]
    require(stored(canonical.initial_canonical_envelope()) == r0)
    head = r0; published = None; admitted = {}; constructed = None
    captures = {row["domain"]: row["emission"] for row in case["captured_evidence"]}
    require(len(captures) == len(case["captured_evidence"]) == 2 and set(captures) == {"domain_A", "domain_B"})
    witnesses = {row["id"]: row for row in policy["witnesses"]}
    programs = {row["id"]: row for row in policy["failure_programs"]}
    fault = policy["canonical_faults"][int(name[1:]) - 1] if name.startswith("C") else None
    expected_exception = policy["canonical_fault_codes"][fault] if fault else programs.get(name, {}).get("underlying_code")
    if expected_exception and not expected_exception.startswith("concurrent_external_"):
        expected_exception = None
    for position, (call, (function, domain)) in enumerate(zip(calls, operations)):
        call = wire(policy, "canonical_call", stored(call))
        args = wire(policy, policy["call_trace_contract"]["dispatch"][function], stored(call["arguments"]))
        require(args["record_raw_utf8"].encode("utf-8") == call["record_before_raw_utf8"].encode("utf-8") == head)
        require(head in (r0, r1))
        record = strict_json(head)
        returned = None; exception = None; installed = None
        if function == "admit_external_input_candidate":
            capture = captures[domain]; require(capture is not None)
            original_raw = artifacts["canonical/QA.json" if domain == "domain_A" else "canonical/QB.json"]
            require(capture["q_raw_utf8"].encode("utf-8") == original_raw)
            expected = strict_json(original_raw)
            if name == "F03":
                expected["target"]["id"] = "shared_slot_02"
            elif name == "F05":
                expected["source"]["source_record_hash"] = canonical.canonical_hash(strict_json(r1))
            elif name == "F06":
                expected["proposed_effect"]["path"] = "/current_causal_state/forbidden_owner"
            if name in {"F03", "F05", "F06"}:
                del expected["evidence"]["evidence_digest"]
                expected["evidence"]["evidence_digest"] = canonical.evidence_digest(expected)
            if name == "F10b" and head == r1:
                expected["input_id"] = "replay_probe_new_input"
            q = strict_json(args["q_object_raw_utf8"].encode("utf-8"))
            raw_q = _base64(args["q_raw_base64"])
            require(stored(q) == stored(expected), "lcer.schema_invalid")
            require(raw_q == (stored(expected)[:-1] if name == "F02" else stored(expected)))
            require(args["materialization_receipt_raw_utf8"] == capture["acceptance_receipt_raw_utf8"]
                    and args["emission_receipt_raw_utf8"] == capture["emission_receipt_raw_utf8"])
            acceptance = strict_json(args["materialization_receipt_raw_utf8"].encode("utf-8"))
            emission = strict_json(args["emission_receipt_raw_utf8"].encode("utf-8"))
            positional = [record, q, raw_q, acceptance, emission]
            before = [v if type(v) is bytes else stored(v) for v in positional]
            try:
                result = canonical.admit_external_input_candidate(record, q, raw_q, acceptance, emission)
                returned = stored(result); admitted[domain] = returned
            except (canonical.CanonicalEnvelopeRejected, canonical.ExternalEvidenceRejected,
                    canonical.RepresentationRejected) as error:
                exception = str(error)
            require(before == [v if type(v) is bytes else stored(v) for v in positional])
        elif function == "construct_bext_from_sealed_fixture_set":
            fixture = strict_json(args["fixture_raw_utf8"].encode("utf-8"))
            require(stored(fixture) == stored(canonical.primary_fixture(strict_json(r0))), "lcer.schema_invalid")
            order = witnesses.get(name, {}).get("presentation", ["domain_A", "domain_B"])
            if name == "F01": order = ["domain_A"]
            if name == "F04a": order = ["domain_A", "domain_A"]
            expected = [strict_json(admitted[key]) for key in order]
            if name == "F04b": expected[1]["physical_event_id"] = expected[0]["physical_event_id"]
            members = [strict_json(raw.encode("utf-8")) for raw in args["presentation_members_raw_utf8"]]
            require(stored(members) == stored(expected), "lcer.schema_invalid")
            before = stored([record, fixture, members])
            try:
                batch, mapping = canonical.construct_bext_from_sealed_fixture_set(record, fixture, members)
                constructed = {"bext_raw_utf8": stored(batch).decode("utf-8"),
                               "admitted_members": [{"input_id": key, "member_raw_utf8": stored(mapping[key]).decode("utf-8")}
                                                    for key in sorted(mapping)]}
                wire(policy, "construction_return", stored(constructed)); returned = stored(constructed)
            except (canonical.CanonicalEnvelopeRejected, canonical.BatchConstructionRejected) as error:
                exception = str(error)
            require(before == stored([record, fixture, members]))
        else:
            require(args["fault_point"] == fault and call["fault_point"] == fault)
            keys = [row["input_id"] for row in args["admitted_members"]]
            require(keys == sorted(set(keys)), "lcer.schema_invalid")
            supplied = {"bext_raw_utf8": args["bext_raw_utf8"], "admitted_members": args["admitted_members"]}
            require(constructed is not None and stored(supplied) == stored(constructed), "lcer.schema_invalid")
            batch = strict_json(args["bext_raw_utf8"].encode("utf-8"))
            mapping = {row["input_id"]: strict_json(row["member_raw_utf8"].encode("utf-8")) for row in args["admitted_members"]}
            before = stored([record, batch, mapping])
            try:
                result = canonical.resolve_external_batch(record, batch, mapping, fault_point=args["fault_point"])
                returned = stored(result)
                require(returned == r1 and published is None)
                head = returned; installed = returned; published = returned
            except (canonical.CanonicalEnvelopeRejected, canonical.BatchResolutionRejected) as error:
                exception = str(error)
            require(before == stored([record, batch, mapping]))
        require(exception == call["exception_code"] == (expected_exception if position == len(calls) - 1 else None))
        require(call["return_raw_utf8"] == (None if returned is None else returned.decode("utf-8")))
        require(call["published_record_raw_utf8"] == (None if installed is None else installed.decode("utf-8")))
        require(call["record_after_raw_utf8"].encode("utf-8") == head)
        require(call["fault_point"] == (fault if function == "resolve_external_batch" else None))
    should_publish = name in witnesses or any(row["id"] == name and row["prefix"] in {"P3", "P4", "P5"}
                                             for row in policy["failure_programs"])
    require((published is not None) == should_publish and head == (r1 if should_publish else r0))
    require(case["canonical_artifacts"] == {"initial_raw_utf8": r0.decode("utf-8"),
                "published_raw_utf8": None if published is None else published.decode("utf-8"),
                "terminal_raw_utf8": head.decode("utf-8")})
    return {"call_count": len(calls), "publication_count": int(published is not None), "terminal_raw_sha256": digest(head)}


def _trace_relations(policy, artifacts, case):
    """Reconcile typed trace events, original streams and repeated case fields."""
    name = case["witness_id"]
    bindings = {row["domain"]: row for row in case["process_bindings"]}
    require(len(bindings) == len(case["process_bindings"]) == 2 and set(bindings) == {"domain_A", "domain_B"})
    for domain, binding in bindings.items():
        wire(policy, "process_binding", stored(binding))
        require(binding["witness_id"] == name and binding["domain"] == domain)
    raw_trace = artifacts[name + "/harness.jsonl"]
    lines = raw_trace.splitlines(keepends=True)
    require(bool(lines))
    events = []; previous = None; clock = 0
    commands = {}; responses = {}; pending = {}; starts = {}; physical = {}; faults = []
    stdin_offsets = {}; stdout_offsets = {}; stdout_seen = set(); observations = []; receipts = []; captured = {}
    allowed_operations = {"bind_0001", "materialize_0001", "emit_0001", "materialize_0002", "arm_fault_0001",
                          "inspect_terminal", "shutdown_0001", *("inspect_L%d" % index for index in range(6))}
    for index, raw in enumerate(lines):
        event = wire(policy, "trace_event", raw)
        require(event["sequence"] == index and event["previous_event_sha256"] == previous
                and event["monotonic_ns"] >= clock)
        previous = digest(raw); clock = event["monotonic_ns"]
        payload = wire(policy, event["event_id"], stored(event["payload"]))
        events.append(event)
        if "domain" in payload:
            require(event["domain"] == payload["domain"])
        if "operation_id" in payload:
            require(event["operation_id"] == payload["operation_id"])
        if event["event_id"] == "fault_event":
            faults.append(payload)
        if event["event_id"] != "wire_event":
            continue
        raw_line = payload["raw_line_utf8"].encode("utf-8")
        message = wire(policy, payload["parsed_schema"], raw_line)
        if payload["parsed_schema"] == "fault_event":
            require(message["failure_case"] == name and message["executor"] == "unreal" and event["domain"] in bindings)
            domain = event["domain"]; launch = bindings[domain]["launch_id"]
            operation = event["operation_id"]
        else:
            require(message["witness_id"] == name and message["domain"] == event["domain"])
            domain = message["domain"]; launch = message["launch_id"]
            operation = message.get("operation_id")
        identity = (domain, launch)
        original = launch == bindings[domain]["launch_id"]
        require(original or (name == "F07" and domain == "domain_A" and payload["parsed_schema"] == "startup"))
        require(event["operation_id"] == operation)
        key = (domain, launch, operation)
        if payload["direction"] == "stdin":
            require(payload["parsed_schema"] == "command" and original)
            require(payload["stream_byte_offset"] == stdin_offsets.get(identity, 0))
            stdin_offsets[identity] = payload["stream_byte_offset"] + len(raw_line)
            require(key not in commands and identity not in pending and identity in starts and operation in allowed_operations)
            expected_binding = digest(stored(bindings[domain]))
            if name == 'F18' and message['command'] == 'materialize' and operation == 'materialize_0002' and domain == 'domain_A':
                expected_binding = '0' * 64
            require(message['binding_sha256'] == expected_binding, 'lcer.binding_mismatch')
            if not any(k[:2] == identity for k in commands):
                require(message["command"] == "bind" and operation == "bind_0001")
            command_type = message["command"]
            argument_schema = {"bind": "process_binding", "materialize": "materialize_input", "arm_fault": "fault_arm"}.get(command_type)
            if argument_schema:
                wire(policy, argument_schema, stored(message["payload"]))
            else:
                require(message["payload"] is None)
            require((command_type == "bind" and operation == "bind_0001")
                    or (command_type == "materialize" and operation in {"materialize_0001", "materialize_0002"})
                    or (command_type == "emit" and operation == "emit_0001")
                    or (command_type == "inspect" and operation.startswith("inspect_"))
                    or (command_type == "arm_fault" and operation == "arm_fault_0001")
                    or (command_type == "shutdown" and operation == "shutdown_0001"))
            commands[key] = message; pending[identity] = key
            continue
        require(payload["direction"] == "stdout" and payload["parsed_schema"] != "command")
        stream_path = name + "/" + (domain if original else "replacement") + ".stdout.log"
        stream = artifacts[stream_path]; offset = payload["stream_byte_offset"]
        require(offset >= stdout_offsets.get(stream_path, 0))
        require(offset == 0 or stream[offset - 1:offset] == b"\n")
        require(stream[offset:offset + len(raw_line)] == raw_line)
        stdout_offsets[stream_path] = offset + len(raw_line)
        occurrence = (stream_path, offset, raw_line)
        require(occurrence not in stdout_seen); stdout_seen.add(occurrence)
        kind = payload["parsed_schema"]
        if kind == "startup":
            require(identity not in starts and identity not in pending)
            starts[identity] = message
        elif kind == "response":
            require(pending.get(identity) == key and key not in responses)
            command = commands[key]
            for field in ("witness_id", "domain", "launch_id", "operation_id", "binding_sha256", "command"):
                require(message[field] == command[field])
            if message["status"] == "error":
                require(message["error"] is not None and message["payload"] is None)
            else:
                require(message["error"] is None and message["payload"] is not None)
                result = wire(policy, policy["schema_contract"]["response_match"][message["command"]], stored(message["payload"]))
                if message["command"] == "inspect": observations.append(result)
                if message["command"] == "materialize": receipts.append(result)
                if message["command"] == "emit":
                    require(key in physical and result["physical_event"] == physical[key] and domain not in captured)
                    captured[domain] = result
            responses[key] = message; del pending[identity]
        elif kind == "physical_event":
            require(pending.get(identity) == key and commands[key]["command"] == "emit" and key not in physical)
            physical[key] = message
        else:
            require(kind == "fault_event" and pending.get(identity) == key)
    require(not pending and set(commands) == set(responses) and len(starts) == (3 if name == "F07" else 2))
    for domain, binding in bindings.items():
        require((domain, binding["launch_id"]) in starts)
    # Recover proof lines from each complete stdout stream, including lines
    # the harness might have omitted from its trace.
    scanned = set()
    for stream_path in policy["artifact_hash_graph"]["case_record_targets"][name]:
        if not stream_path.endswith(".stdout.log"):
            continue
        offset = 0
        for raw in artifacts[stream_path].splitlines(keepends=True):
            if raw.lstrip().startswith(b"{"):
                message = strict_json(raw)
                require(sum(schema_accepts(policy["wire_schemas"], policy["wire_schemas"][kind], message)
                            for kind in ("startup", "response", "physical_event", "fault_event")) == 1)
                scanned.add((stream_path, offset, raw))
            offset += len(raw)
    require(scanned == stdout_seen and case["command_trace"] == events)
    require(case["liveness_checkpoints"] == [row["payload"] for row in events if row["event_id"] == "liveness"])
    require(case["head_dispositions"] == [row["payload"] for row in events if row["event_id"] == "head_event"])
    require(case["live_observations"] == observations and case["materialization_receipts"] == receipts)
    captures = {row["domain"]: row["emission"] for row in case["captured_evidence"]}
    require(len(captures) == len(case["captured_evidence"]) == 2 and set(captures) == {"domain_A", "domain_B"})
    require(captures == {domain: captured.get(domain) for domain in bindings})
    require(set(physical) == {key for key, response in responses.items() if response["command"] == "emit" and response["status"] == "ok"})
    return {"events": events, "commands": commands, "responses": responses, "startups": starts,
            "physical_events": physical, "faults": faults}


def _liveness_series_relations(policy, supplied, initial_checkpoint='startup'):
    """Check one launch's retained process and pipe records independently.

    Callers still owe raw-trace authentication, initial binding/build/world
    checks and the case's exact operation schedule. Identical observations
    cannot establish that the acquisition reader actually sampled the kernel;
    that boundary also requires the source audit. Dynamic engine descriptors
    and open-file bytes may change. Original launch inputs and proof pipes may
    not. No producer helper or summary flag participates in this calculation.
    """
    require(initial_checkpoint in ('startup', 'terminal') and type(supplied) is list and bool(supplied),
            'lcer.liveness_invalid')
    samples = [wire(policy, 'liveness', stored(row)) for row in supplied]
    initial = samples[0]
    require(initial['checkpoint'] == initial_checkpoint and initial['poll_returncode'] is None and
            initial['observed_process'] is not None, 'lcer.liveness_invalid')
    process = initial['observed_process']
    child, parent = process['pid'], process['ppid']
    require(child > 0 and parent > 0 and child != parent, 'lcer.original_process_identity_mismatch')

    def pipes(rows):
        result = {}
        for row in rows:
            require(row['kind'] == 'pipe' and row['path'] is None and row['pid'] > 0 and
                    re.fullmatch('[0-9a-f]{16}', row['kernel_id']) is not None and row['kernel_id'] != '0' * 16 and
                    (row['peer_kernel_id'] is None or
                     re.fullmatch('[0-9a-f]{16}', row['peer_kernel_id']) is not None),
                    'lcer.original_pipe_identity_mismatch')
            key = (row['pid'], row['fd'])
            require(key not in result, 'lcer.original_pipe_identity_mismatch')
            result[key] = row
        return result

    original = pipes(initial['pipe_endpoints'])
    child_pipes = {key: row for key, row in original.items() if key[0] == child}
    parent_pipes = {key: row for key, row in original.items() if key[0] == parent}
    require(set(child_pipes) == {(child, number) for number in (0, 1, 2)} and
            len(parent_pipes) == 3 and len(original) == 6 and
            all(number >= 3 for _, number in parent_pipes) and
            len({row['kernel_id'] for row in original.values()}) == 6,
            'lcer.original_pipe_identity_mismatch')
    for number, access in enumerate(('read', 'write', 'write')):
        row = child_pipes[(child, number)]
        peers = [peer for peer in parent_pipes.values() if peer['kernel_id'] == row['peer_kernel_id']]
        require(len(peers) == 1 and row['access'] == access and
                peers[0]['peer_kernel_id'] == row['kernel_id'] and
                peers[0]['access'] == ('write' if access == 'read' else 'read'),
                'lcer.original_pipe_identity_mismatch')
    departed = {key: dict(row, peer_kernel_id=None) for key, row in parent_pipes.items()}
    order = {name: number for number, name in enumerate(
        ('startup', 'L0', 'L1', 'L2', 'before_resolve', 'after_resolve', 'L3', 'L4', 'L5', 'terminal', 'cleanup'))}
    previous = -1
    exit_code = None
    stable_fields = ('pid', 'ppid', 'macos_birth_tuple', 'cwd_realpath', 'executable',
                     'argv', 'environment', 'loaded_images', 'startup')
    for sample in samples:
        require(sample['domain'] == initial['domain'] and sample['launch_id'] == initial['launch_id'],
                'lcer.original_process_identity_mismatch')
        position = order[sample['checkpoint']]
        require(position > previous, 'lcer.liveness_sequence_invalid')
        previous = position
        code = sample['poll_returncode']
        observed = sample['observed_process']
        require((code is None) == (observed is not None), 'lcer.liveness_invalid')
        if exit_code is not None:
            require(code == exit_code, 'lcer.original_process_identity_mismatch')
        if code is not None:
            exit_code = code
        expected = original if code is None else departed
        endpoints, holders = pipes(sample['pipe_endpoints']), pipes(sample['pipe_holders'])
        require(endpoints == expected, 'lcer.original_pipe_identity_mismatch')
        require(not (set(holders) - set(expected)), 'lcer.proof_pipe_extra_holder')
        require(holders == expected, 'lcer.original_pipe_identity_mismatch')
        if observed is None:
            continue
        require(all(same_json(observed[field], process[field]) for field in stable_fields),
                'lcer.original_process_identity_mismatch')
        startup = observed['startup']
        require(startup['pid'] == child and startup['domain'] == sample['domain'] and
                startup['launch_id'] == sample['launch_id'] and
                startup['cwd_realpath'] == observed['cwd_realpath'] and
                same_json(startup['loaded_images'], observed['loaded_images']),
                'lcer.original_process_identity_mismatch')
        descriptors = observed['descriptors']
        numbers = [row['fd'] for row in descriptors]
        require(numbers == sorted(set(numbers)) and all(row['pid'] == child for row in descriptors),
                'lcer.process_observation_invalid')
        actual = {(child, row['fd']): row for row in descriptors if row['fd'] in (0, 1, 2)}
        require(actual == child_pipes, 'lcer.original_pipe_identity_mismatch')
        # A duplicated original pipe is forbidden even if omitted from the
        # separate holder inventory. Other engine descriptors remain dynamic.
        original_ids = {row['kernel_id'] for row in original.values()}
        require(not any(row['fd'] > 2 and row['kind'] == 'pipe' and
                        (row['kernel_id'] in original_ids or row['peer_kernel_id'] in original_ids)
                        for row in descriptors), 'lcer.proof_pipe_extra_holder')
        files = observed['open_files']
        names = [row['realpath'] for row in files]
        require(names == sorted(set(names)) and set(names) ==
                {row['path'] for row in descriptors if row['kind'] == 'vnode'},
                'lcer.process_observation_invalid')
    return samples


def _liveness_trace_relations(policy, case, trace):
    """Join reconciled trace samples to bindings and the frozen checkpoints.

    The caller obtains trace from _trace_relations. This checks liveness and
    its trace placement; canonical, world, fault-action and build acceptance
    remain separate. It never treats case status or a producer flag as proof.
    """
    name = case['witness_id']
    witnesses = {row['id'] for row in policy['witnesses']}
    programs = {row['id']: row for row in policy['failure_programs']}
    canonical_faults = {'C%02d' % (number + 1) for number in range(len(policy['canonical_faults']))}
    require(name in witnesses | set(programs) | canonical_faults, 'lcer.liveness_invalid')
    bindings = {row['domain']: wire(policy, 'process_binding', stored(row)) for row in case['process_bindings']}
    require(len(case['process_bindings']) == 2 and set(bindings) == {'domain_A', 'domain_B'},
            'lcer.binding_mismatch')
    originals = {(domain, binding['launch_id']): binding for domain, binding in bindings.items()}
    events = trace['events']
    samples = {}; sample_positions = {}; starts = {}; bind_positions = {}; process_positions = set()
    for position, supplied in enumerate(events):
        event = wire(policy, 'trace_event', stored(supplied))
        payload = event['payload']
        if event['event_id'] == 'process_observation':
            process_positions.add(position)
            continue
        if event['event_id'] == 'wire_event':
            message = wire(policy, payload['parsed_schema'], payload['raw_line_utf8'].encode('utf-8'))
            if payload['parsed_schema'] == 'startup':
                key = (message['domain'], message['launch_id'])
                require(key not in starts, 'lcer.liveness_invalid')
                starts[key] = (position, message, payload['raw_line_utf8'].encode('utf-8'))
            elif payload['parsed_schema'] == 'command' and message['command'] == 'bind':
                key = (message['domain'], message['launch_id'])
                require(key in originals and key not in bind_positions and same_json(message['payload'], originals[key]),
                        'lcer.binding_mismatch')
                bind_positions[key] = position
            continue
        if event['event_id'] != 'liveness':
            continue
        row = wire(policy, 'liveness', stored(payload))
        require(event['domain'] == row['domain'] and event['operation_id'] is None, 'lcer.liveness_invalid')
        key = (row['domain'], row['launch_id'])
        samples.setdefault(key, []).append(row)
        sample_positions.setdefault(key, []).append(position)
        if row['observed_process'] is not None:
            require(position > 0 and position - 1 in process_positions, 'lcer.liveness_invalid')
            observed_event = events[position - 1]
            require(observed_event['domain'] == row['domain'] and observed_event['operation_id'] is None and
                    same_json(observed_event['payload'], row['observed_process']), 'lcer.liveness_invalid')
            process_positions.remove(position - 1)
    require(not process_positions and same_json(case['liveness_checkpoints'],
            [row['payload'] for row in events if row['event_id'] == 'liveness']), 'lcer.liveness_invalid')
    require(set(starts) == set(samples) and set(bind_positions) == set(originals), 'lcer.liveness_invalid')
    extras = set(samples) - set(originals)
    require(set(originals) <= set(samples) and len(extras) == (1 if name == 'F07' else 0), 'lcer.liveness_invalid')
    expected = ['startup', 'L0']
    prefix = 5 if name in witnesses else 2 if name in canonical_faults else int(programs[name]['prefix'][1])
    for number in range(1, prefix + 1):
        if number == 3:
            expected.extend(('before_resolve', 'after_resolve'))
        expected.append('L%d' % number)
    if name in canonical_faults:
        expected.extend(('before_resolve', 'after_resolve'))
    if name not in witnesses:
        expected.append('terminal')
    expected.append('cleanup')
    dead_domain = {'F07': 'domain_A', 'F08': 'domain_B', 'F11': 'domain_A', 'F12': 'domain_B'}.get(name)
    parent = None; original_pids = set(); parent_fds = set(); kernel_ids = set()
    for key, binding in originals.items():
        rows = _liveness_series_relations(policy, samples[key])
        require([row['checkpoint'] for row in rows] == expected, 'lcer.liveness_sequence_invalid')
        process = rows[0]['observed_process']
        require(binding['witness_id'] == name and binding['pid'] == process['pid'] and
                same_json(binding['macos_birth_tuple'], process['macos_birth_tuple']), 'lcer.binding_mismatch')
        position, startup, startup_raw = starts[key]
        require(position < sample_positions[key][0] < bind_positions[key] and
                same_json(startup, process['startup']) and binding['startup_sha256'] == digest(startup_raw),
                'lcer.binding_mismatch')
        proof = [row for row in process['descriptors'] if row['fd'] in (0, 1, 2)]
        require(binding['descriptor_map_sha256'] == digest(stored(proof)), 'lcer.binding_mismatch')
        require(process['pid'] not in original_pids and (parent is None or process['ppid'] == parent),
                'lcer.original_process_identity_mismatch')
        original_pids.add(process['pid']); parent = process['ppid']
        current_fds = {row['fd'] for row in rows[0]['pipe_endpoints'] if row['pid'] == parent}
        current_ids = {row['kernel_id'] for row in rows[0]['pipe_endpoints']}
        require(not (current_fds & parent_fds or current_ids & kernel_ids), 'lcer.original_pipe_identity_mismatch')
        parent_fds.update(current_fds); kernel_ids.update(current_ids)
        for row in rows:
            exited = row['checkpoint'] == 'cleanup' or (row['checkpoint'] == 'terminal' and key[0] == dead_domain)
            require((row['poll_returncode'] is not None) == exited, 'lcer.terminal_process_invalid')
    # Each paired checkpoint completes before the next pair. The contract
    # fixes observe/bind A before B at startup; later liveness pairs need no
    # extra ordering rule between the two independent kernel samples.
    a = ('domain_A', bindings['domain_A']['launch_id'])
    b = ('domain_B', bindings['domain_B']['launch_id'])
    previous = -1
    for left, right in zip(sample_positions[a], sample_positions[b]):
        require(previous < min(left, right), 'lcer.liveness_sequence_invalid')
        previous = max(left, right)
    require(sample_positions[a][0] < bind_positions[a] < sample_positions[b][0], 'lcer.liveness_sequence_invalid')
    if extras:
        replacement, = extras
        require(replacement[0] == 'domain_A' and replacement[1] != a[1], 'lcer.original_process_identity_mismatch')
        faults = [(number, event['payload']) for number, event in enumerate(events)
                  if event['event_id'] == 'fault_event' and event['payload']['failure_case'] == 'F07']
        require(len(faults) == 1, 'lcer.liveness_invalid')
        position, fault = faults[0]
        require(fault['executor'] == 'harness' and fault['after']['kind'] == 'process', 'lcer.liveness_invalid')
        initial = fault['after']['sample']
        require(initial['domain'] == replacement[0] and initial['launch_id'] == replacement[1] and
                [row['checkpoint'] for row in samples[replacement]] == ['cleanup'] and
                starts[replacement][0] < position < sample_positions[replacement][0], 'lcer.liveness_invalid')
        rows = _liveness_series_relations(policy, [initial] + samples[replacement], initial_checkpoint='terminal')
        process = rows[0]['observed_process']
        require(process['ppid'] == parent and process['pid'] != bindings['domain_B']['pid'] and
                (process['pid'], process['macos_birth_tuple']) != (bindings['domain_A']['pid'], bindings['domain_A']['macos_birth_tuple']) and
                same_json(process['startup'], starts[replacement][1]), 'lcer.original_process_identity_mismatch')
        current_fds = {row['fd'] for row in rows[0]['pipe_endpoints'] if row['pid'] == parent}
        current_ids = {row['kernel_id'] for row in rows[0]['pipe_endpoints']}
        require(not (current_fds & parent_fds or current_ids & kernel_ids), 'lcer.original_pipe_identity_mismatch')
        require(rows[-1]['poll_returncode'] is not None, 'lcer.terminal_process_invalid')
    return samples


def _operation_schedule_relations(policy, case, trace):
    """Check phase order across original streams, canonical calls and samples.

    Call after raw-stream reconciliation. This predicate checks scheduling,
    response outcomes and fault placement. It does not replace canonical
    replay, materialization-byte authentication, world/fault comparison,
    process observations, source audit or build provenance.
    """
    name = case['witness_id']
    witnesses = {row['id']: row for row in policy['witnesses']}
    programs = {row['id']: row for row in policy['failure_programs']}
    canonical_faults = {'C%02d' % (number + 1) for number in range(len(policy['canonical_faults']))}
    require(name in set(witnesses) | set(programs) | canonical_faults, 'lcer.operation_sequence_invalid')
    domains = ('domain_A', 'domain_B')
    bindings = {row['domain']: row for row in case['process_bindings']}
    require(set(bindings) == set(domains) and len(case['process_bindings']) == 2, 'lcer.binding_mismatch')
    originals = {(domain, row['launch_id']) for domain, row in bindings.items()}
    witness = witnesses.get(name, {})
    program = programs.get(name)
    child_fault = program is not None and program['executor'] == 'unreal'
    events = trace['events']
    require(bool(events) and events[-1]['monotonic_ns'] - events[0]['monotonic_ns'] <= 900 * 10**9,
            'lcer.case_timeout')
    tokens = []; pending = None; pending_faults = 0; request_time = None
    for supplied in events:
        event = wire(policy, 'trace_event', stored(supplied))
        kind, payload, domain = event['event_id'], event['payload'], event['domain']
        if kind == 'wire_event':
            message = wire(policy, payload['parsed_schema'], payload['raw_line_utf8'].encode('utf-8'))
            wire_kind = payload['parsed_schema']
            if wire_kind == 'command':
                require(pending is None and (domain, message['launch_id']) in originals,
                        'lcer.operation_sequence_invalid')
                pending = message; pending_faults = 0; request_time = event['monotonic_ns']
                if message['command'] == 'arm_fault':
                    require(child_fault and domain == program['domain'] and same_json(message['payload'],
                            {'failure_case': name, 'stage': program['stage'], 'operation_id': 'materialize_0002'}),
                            'lcer.fault_arm_invalid')
                continue
            if wire_kind == 'startup':
                require(pending is None, 'lcer.operation_sequence_invalid')
                original = (domain, message['launch_id']) in originals
                require(original or (name == 'F07' and domain == 'domain_A'), 'lcer.original_process_identity_mismatch')
                tokens.append(('startup' if original else 'replacement_startup', domain))
                continue
            require(pending is not None and domain == pending['domain'], 'lcer.operation_sequence_invalid')
            if wire_kind == 'fault_event':
                require(child_fault and domain == program['domain'] and pending['command'] == 'materialize' and
                        pending['operation_id'] == 'materialize_0002' and pending_faults == 0 and
                        message['failure_case'] == name and message['consumed'] is True and
                        all(message[key] == program[key] for key in ('executor', 'stage', 'action', 'underlying_code')),
                        'lcer.fault_event_invalid')
                pending_faults += 1
                continue
            if wire_kind == 'physical_event':
                require(pending['command'] == 'emit', 'lcer.operation_sequence_invalid')
                continue
            require(wire_kind == 'response' and all(message[key] == pending[key] for key in
                    ('domain', 'launch_id', 'operation_id', 'command', 'binding_sha256', 'witness_id')),
                    'lcer.operation_sequence_invalid')
            require(0 <= event['monotonic_ns'] - request_time <= 60 * 10**9, 'lcer.operation_timeout')
            expected_fault = child_fault and domain == program['domain'] and pending['operation_id'] == 'materialize_0002'
            require(pending_faults == int(expected_fault), 'lcer.fault_event_invalid')
            failure = None
            if name in ('F09', 'F13', 'F14', 'F17', 'F18') and pending['operation_id'] == 'materialize_0002':
                require(domain == program['domain'], 'lcer.operation_sequence_invalid')
                failure = program['underlying_code']
            require(message['status'] == ('error' if failure else 'ok'), 'lcer.unexpected_failure_outcome')
            require((message['error'] is None) if failure is None else
                    (message['error'] is not None and message['error']['underlying_code'] == failure),
                    'lcer.unexpected_failure_outcome')
            if failure is None:
                result = wire(policy, policy['schema_contract']['response_match'][pending['command']], stored(message['payload']))
                require(all(result[field] == pending[field] for field in
                            ('witness_id', 'domain', 'launch_id', 'operation_id', 'binding_sha256') if field in result),
                        'lcer.protocol_response_mismatch')
                if pending['command'] == 'bind':
                    require(result['startup_sha256'] == pending['payload']['startup_sha256'], 'lcer.binding_mismatch')
                if pending['command'] == 'arm_fault':
                    require(result['failure_case'] == name and result['stage'] == program['stage'] and
                            result['armed_for'] == 'materialize_0002', 'lcer.fault_arm_invalid')
            tokens.append(('command', pending['command'], pending['operation_id'], domain))
            pending = None
            continue
        require(pending is None, 'lcer.operation_sequence_invalid')
        if kind == 'process_observation':
            continue
        if kind == 'canonical_call':
            tokens.append(('canonical', payload['function'], domain))
        elif kind == 'liveness':
            original = (payload['domain'], payload['launch_id']) in originals
            require(original or (name == 'F07' and payload['domain'] == 'domain_A' and payload['checkpoint'] == 'cleanup'),
                    'lcer.original_process_identity_mismatch')
            tokens.append(('live', payload['checkpoint'], domain if original else 'replacement'))
        elif kind == 'head_event':
            tokens.append(('head', payload['edge'], domain, payload['observation_sha256'] is not None))
        else:
            require(kind == 'fault_event' and program is not None and not child_fault and domain == program['domain'] and
                    payload['failure_case'] == name and payload['consumed'] is True and
                    all(payload[key] == program[key] for key in ('executor', 'stage', 'action', 'underlying_code')),
                    'lcer.fault_event_invalid')
            tokens.append(('fault', domain))
    require(pending is None, 'lcer.operation_sequence_invalid')

    # Preserve each complete pair without inventing an order between its two
    # independent samples or classifications. Startup and cleanup stay separate.
    actual = []; index = 0
    while index < len(tokens):
        token = tokens[index]
        paired_live = token[0] == 'live' and token[1] not in ('startup', 'cleanup')
        paired_head = token[0] == 'head' and token[1] in ('classify', 'invalidate_claims', 'terminal')
        if paired_live or paired_head:
            require(index + 1 < len(tokens), 'lcer.operation_sequence_invalid')
            peer = tokens[index + 1]
            require(peer[:2] == token[:2] and {token[2], peer[2]} == set(domains) and
                    (token[:2] == ('head', 'terminal') or peer[3:] == token[3:]),
                    'lcer.operation_sequence_invalid')
            if token[:2] == ('head', 'terminal'):
                actual.append(('head_terminal_pair', tuple(sorted(((token[2], token[3]), (peer[2], peer[3]))))))
            else:
                actual.append((token[0] + '_pair', token[1], *token[3:]))
            index += 2
        else:
            actual.append(token); index += 1

    expected = [('head', 'initialize', None, False)]
    def command(kind, operation, domain):
        expected.append(('command', kind, operation, domain))
    def canonical(function, domain=None):
        expected.append(('canonical', function, domain))
    admission = 'admit_external_input_candidate'
    construction = 'construct_bext_from_sealed_fixture_set'
    resolution = 'resolve_external_batch'
    def expand(prefix):
        for operation in policy['operation_schedule']['prefixes'][prefix]:
            if operation in policy['operation_schedule']['prefixes']:
                expand(operation)
            elif operation in ('launch A', 'launch B'):
                # Launch ownership is proved by process observations/source;
                # the trace's first launch-visible event is the ready message.
                continue
            elif operation in ('ready A', 'ready B'):
                expected.append(('startup', domains[int(operation.endswith('B'))]))
            elif operation in ('observe and bind A', 'observe and bind B'):
                domain = domains[int(operation.endswith('B'))]
                expected.append(('live', 'startup', domain)); command('bind', 'bind_0001', domain)
            elif operation.startswith('materialize_0001 '):
                require(operation in ('materialize_0001 A', 'materialize_0001 B'), 'lcer.operation_sequence_invalid')
                command('materialize', 'materialize_0001', domains[int(operation.endswith('B'))])
            elif operation.startswith('inspect_L'):
                match = re.fullmatch(r'inspect_(L[0-5]) ([AB])', operation)
                require(match is not None, 'lcer.operation_sequence_invalid')
                command('inspect', 'inspect_' + match[1], domains[int(match[2] == 'B')])
            elif operation.startswith('liveness L'):
                require(operation[-2:] in ('L0', 'L1', 'L2', 'L3', 'L4', 'L5'), 'lcer.operation_sequence_invalid')
                expected.extend((('head_pair', 'classify', True), ('live_pair', operation[-2:])))
            elif operation in ('emit_0001 A', 'emit_0001 B'):
                command('emit', 'emit_0001', witness.get('emission', domains)[int(operation.endswith('B'))])
            elif operation in ('admit QA on R0', 'admit QB on R0'):
                canonical(admission, witness.get('presentation', domains)[int(operation == 'admit QB on R0')])
            elif operation == 'construct primary fixture batch': canonical(construction)
            elif operation == 'invalidate both current claims': expected.append(('head_pair', 'invalidate_claims', False))
            elif operation in ('liveness before_resolve', 'liveness after_resolve'):
                expected.append(('live_pair', operation.split()[1]))
            elif operation == 'resolve once and publish exact R1':
                canonical(resolution); expected.append(('head', 'publish', None, False))
            elif operation == 'classify both stale': expected.append(('head_pair', 'classify', False))
            elif operation in ('materialize_0002 first refresh domain', 'materialize_0002 second refresh domain'):
                command('materialize', 'materialize_0002', witness.get('refresh', domains)[int('second' in operation)])
            else:
                require(False, 'lcer.operation_sequence_invalid')
    expand('P5' if name in witnesses else program['prefix'] if program else 'P2')
    if name in canonical_faults:
        expected.append(('live_pair', 'before_resolve')); canonical(resolution)
        expected.append(('live_pair', 'after_resolve'))
    elif program:
        if name in ('F01', 'F08'): command('emit', 'emit_0001', 'domain_A')
        if name == 'F01': canonical(admission, 'domain_A'); canonical(construction)
        elif name in ('F02', 'F03', 'F05', 'F06', 'F10a', 'F10b'): canonical(admission, 'domain_A')
        elif name in ('F04a', 'F04b'):
            canonical(admission, 'domain_A'); canonical(admission, 'domain_B'); canonical(construction)
        elif name == 'F07': expected.append(('replacement_startup', 'domain_A'))
        elif name in ('F09', 'F17', 'F18'): command('materialize', 'materialize_0002', program['domain'])
        elif child_fault:
            command('arm_fault', 'arm_fault_0001', program['domain'])
            command('materialize', 'materialize_0002', program['domain'])
            if name in ('F15', 'F16a', 'F16b'):
                for domain in domains: command('inspect', 'inspect_L4', domain)
        else:
            require(name in ('F08', 'F11', 'F12'), 'lcer.operation_sequence_invalid')
        if not child_fault: expected.append(('fault', program['domain']))
    dead_domain = {'F07': 'domain_A', 'F08': 'domain_B', 'F11': 'domain_A', 'F12': 'domain_B'}.get(name)
    if name not in witnesses:
        for domain in domains:
            if domain != dead_domain: command('inspect', 'inspect_terminal', domain)
        expected.extend((('live_pair', 'terminal'),
                         ('head_terminal_pair', tuple((domain, domain != dead_domain) for domain in domains))))
    require(actual[:len(expected)] == expected, 'lcer.operation_sequence_invalid')
    shutdowns = set(); cleaned = set()
    for token in actual[len(expected):]:
        if token[0] == 'command':
            require(token[1:3] == ('shutdown', 'shutdown_0001') and token[3] in domains and
                    token[3] != dead_domain and token[3] not in shutdowns | cleaned, 'lcer.operation_sequence_invalid')
            shutdowns.add(token[3])
        else:
            require(token[:2] == ('live', 'cleanup') and token[2] not in cleaned and
                    (token[2] in shutdowns or token[2] == dead_domain or (name == 'F07' and token[2] == 'replacement')),
                    'lcer.operation_sequence_invalid')
            cleaned.add(token[2])
    require(shutdowns == set(domains) - {dead_domain} and
            cleaned == set(domains) | ({'replacement'} if name == 'F07' else set()), 'lcer.case_cleanup_incomplete')
    return actual


def _materialization_relations(policy, artifacts, case, trace, canonical):
    """Derive materialization bytes and receipts from pinned canonical records.

    Call with reconciled streams and an authenticated immutable canonical
    module. Scheduling, actual fault actions and native world/Actor receipt
    joins remain separate predicates. No candidate constructor is invoked.
    """
    name = case['witness_id']
    require(name in policy['artifact_hash_graph']['case_ids'])
    records = {}
    for role in ('R0', 'R1'):
        raw = artifacts['canonical/' + role + '.json']
        path = 'proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_' + role + '.json'
        require(digest(raw) == policy['canonical_records'][path])
        record = strict_json(raw)
        require(canonical.stored_payload_bytes(record) == raw and not canonical.validate_canonical_envelope(record))
        records[role] = (raw, record)
    r0, initial = records['R0']; r1, successor = records['R1']
    require(same_json(initial, canonical.initial_canonical_envelope()))
    ancestry = successor['causal_provenance']['canonical_ancestry']
    require(ancestry['parent_record_hash'] == canonical.canonical_hash(initial) and
            ancestry['boundary_derivation'] == 'external_arbitration_batch' and
            initial['current_causal_state']['shared_slot']['allocation_owner'] is None and
            successor['current_causal_state']['shared_slot']['allocation_owner'] == 'domain_A')
    bindings = {row['domain']: wire(policy, 'process_binding', stored(row)) for row in case['process_bindings']}
    require(set(bindings) == {'domain_A', 'domain_B'} and len(case['process_bindings']) == 2)
    require(all(row['witness_id'] == name for row in bindings.values()))

    def expected_command(domain, operation, role):
        binding = bindings[domain]
        raw, record = records[role]
        route = {field: binding[field] for field in ('witness_id', 'domain', 'launch_id')}
        route.update(operation_id=operation, binding_sha256=digest(stored(binding)))
        projection = dict(route, schema='city.live_evidence_projection.v1', record_role=role,
                          record_raw_sha256=digest(raw), record_canonical_hash=canonical.canonical_hash(record),
                          generation=0 if role == 'R0' else 1,
                          allocation_owner=record['current_causal_state']['shared_slot']['allocation_owner'])
        payload = {'projection': projection, 'record_raw_utf8': raw.decode('utf-8'),
                   'launch_receipt_raw_utf8': canonical.stored_receipt_bytes(canonical.launch_receipt(initial)).decode('utf-8')
                   if role == 'R0' else None}
        return dict(route, schema='city.live_evidence_command.v1', command='materialize', payload=payload)

    bound = set(); emitted = set(); represented = {}; pending = {}; outcomes = []
    head = r0; published = False

    def authenticate(command):
        domain, operation = command['domain'], command['operation_id']
        binding = bindings[domain]
        require(all(command[field] == binding[field] for field in ('witness_id', 'domain', 'launch_id')) and
                command['binding_sha256'] == digest(stored(binding)), 'lcer.binding_mismatch')
        payload = wire(policy, 'materialize_input', stored(command['payload']))
        raw = payload['record_raw_utf8'].encode('utf-8')
        parsed = strict_json(raw)
        require(canonical.stored_payload_bytes(parsed) == raw, 'lcer.committed_record_required')
        require(raw in (r0, r1), 'lcer.committed_record_required')
        role = 'R0' if raw == r0 else 'R1'
        wanted = expected_command(domain, operation, role)['payload']
        projection = payload['projection']
        require(all(projection[field] == command[field] for field in
                    ('witness_id', 'domain', 'launch_id', 'operation_id', 'binding_sha256')), 'lcer.binding_mismatch')
        require(same_json(projection, wanted['projection']), 'lcer.committed_record_required')
        receipt_raw = payload['launch_receipt_raw_utf8']
        if role == 'R0':
            require(type(receipt_raw) is str, 'lcer.committed_record_required')
            receipt_bytes = receipt_raw.encode('utf-8')
            receipt = strict_json(receipt_bytes)
            require(canonical.stored_receipt_bytes(receipt) == receipt_bytes, 'lcer.committed_record_required')
            try:
                accepted = canonical.validate_launch_artifact(raw, receipt_bytes)
            except canonical.RepresentationRejected as error:
                raise ValueError('lcer.committed_record_required') from error
            require(same_json(accepted, initial), 'lcer.committed_record_required')
        else:
            # R1 never enters the predecessor's R0-only launch validator.
            require(receipt_raw is None, 'lcer.committed_record_required')
        require(domain in bound and
                ((operation == 'materialize_0001' and role == 'R0' and domain not in represented and domain not in emitted) or
                 (operation == 'materialize_0002' and role == 'R1' and represented.get(domain) == 'R0' and domain in emitted)),
                'lcer.immediate_successor_required')
        return role

    for event in trace['events']:
        if event['event_id'] == 'canonical_call':
            call = wire(policy, 'canonical_call', stored(event['payload']))
            if call['function'] == 'resolve_external_batch' and call['exception_code'] is None:
                require(not published and call['record_before_raw_utf8'].encode() == r0 and
                        call['return_raw_utf8'] == call['published_record_raw_utf8'] == call['record_after_raw_utf8'] == r1.decode())
                head = r1; published = True
            continue
        if event['event_id'] != 'wire_event': continue
        envelope = event['payload']
        kind = envelope['parsed_schema']
        if kind not in ('command', 'response'): continue
        message = wire(policy, kind, envelope['raw_line_utf8'].encode('utf-8'))
        domain, operation = message['domain'], message['operation_id']
        require(domain in bindings and message['launch_id'] == bindings[domain]['launch_id'])
        key = (domain, operation)
        if kind == 'command':
            require(key not in pending)
            role = None; error = None
            if message['command'] == 'bind':
                require(same_json(message['payload'], bindings[domain]))
            if message['command'] == 'materialize':
                try:
                    role = authenticate(message)
                except ValueError as failure:
                    error = str(failure)
                    if error not in ('lcer.binding_mismatch', 'lcer.committed_record_required', 'lcer.immediate_successor_required'):
                        raise
                rejected_input = name in ('F09', 'F17', 'F18') and operation == 'materialize_0002'
                if rejected_input:
                    require(domain == 'domain_A')
                    wanted = expected_command(domain, operation, 'R0' if name == 'F17' else 'R1')
                    if name == 'F09':
                        working = canonical.working_state_projection(initial, initial['current_causal_state'], initial['future_causal_state'])
                        wanted['payload']['record_raw_utf8'] = canonical.stored_payload_bytes(working).decode('utf-8')
                    if name == 'F18': wanted['binding_sha256'] = '0' * 64
                    require(stored(message) == stored(wanted))
                    expected_error = {'F09': 'lcer.committed_record_required', 'F17': 'lcer.immediate_successor_required',
                                      'F18': 'lcer.binding_mismatch'}[name]
                    require(error == expected_error)
                else:
                    require(error is None and role is not None)
                    require(records[role][0] == head)
            pending[key] = (message, role, error)
            continue
        require(key in pending)
        command, role, error = pending.pop(key)
        require(all(message[field] == command[field] for field in
                    ('witness_id', 'domain', 'launch_id', 'operation_id', 'binding_sha256', 'command')))
        if command['command'] == 'bind' and message['status'] == 'ok':
            require(domain not in bound); bound.add(domain)
        if command['command'] == 'emit' and message['status'] == 'ok':
            require(represented.get(domain) == 'R0' and domain not in emitted); emitted.add(domain)
        if command['command'] != 'materialize': continue
        response_error = None if message['error'] is None else message['error']['underlying_code']
        partial = name in ('F13', 'F14') and operation == 'materialize_0002'
        if error is not None or partial:
            if partial:
                require(error is None and role == 'R1' and domain == ('domain_A' if name == 'F13' else 'domain_B'))
            require(message['status'] == 'error' and message['payload'] is None and
                    response_error == (error or 'lcer.injected_partial_publication'))
        else:
            require(message['status'] == 'ok' and response_error is None)
            result = wire(policy, 'materialization_result', stored(message['payload']))
            if role == 'R0':
                require(result['r1_representation'] is None and type(result['r0_acceptance_raw_utf8']) is str)
                raw = result['r0_acceptance_raw_utf8'].encode('utf-8')
                receipt = strict_json(raw)
                require(canonical.stored_receipt_bytes(receipt) == raw)
                wanted = canonical.materialization_acceptance_receipt(initial, domain, bindings[domain]['launch_id'])
                require(raw == canonical.stored_receipt_bytes(wanted))
            else:
                require(role == 'R1' and result['r0_acceptance_raw_utf8'] is None and result['r1_representation'] is not None)
                receipt = result['r1_representation']
                projection = command['payload']['projection']
                require(all(receipt[field] == projection[field] for field in
                            ('witness_id', 'domain', 'launch_id', 'operation_id', 'binding_sha256', 'record_raw_sha256',
                             'record_canonical_hash', 'generation', 'allocation_owner')))
                require(receipt['anchor_actor_id'] != receipt['resource_actor_id'] and receipt['proposal_capability_enabled'] is False)
            represented[domain] = role
        outcomes.append({'domain': domain, 'operation_id': operation, 'record_role': role,
                         'authentication_error': error, 'response_error': response_error})
    require(not pending)
    return outcomes


def _inherits(class_path, ancestor, class_parents):
    """Follow an independently authenticated class graph; never guess from names."""
    visited = set()
    while class_path is not None:
        require(class_path not in visited and class_path in class_parents)
        if class_path == ancestor:
            return True
        visited.add(class_path); class_path = class_parents[class_path]
    return False


def _world_facts(policy, worlds, class_parents):
    """Keep invalid physical rows. Raw completeness and display validity differ."""
    rows = []; world_paths = []; actor_ids = []
    relevant = []; pawns = []; controllers = []
    for supplied in worlds:
        world = wire(policy, "world_row", stored(supplied))
        world_paths.append(world["world_path"])
        size = world["actor_array_size"]; nulls = world["null_slots"]
        require(type(size) is int and world["visited_slots"] == list(range(size)))
        require(all(type(slot) is int and 0 <= slot < size for slot in nulls)
                and len(nulls) == len(set(nulls)) and len(world["actors"]) == size - len(nulls))
        names = [row["actor_path"] for row in world["actors"]]
        require(names == sorted(set(names)))
        for actor in world["actors"]:
            require(actor["world_path"] == world["world_path"]
                    and actor["actor_id"] == actor["world_path"] + "|" + actor["actor_path"])
            require(actor["actor_path"].startswith(world["world_path"] + ":"))
            actor_ids.append(actor["actor_id"]); rows.append(actor)
            proof_class = _inherits(actor["class_path"], "/Script/CityLiveEvidenceProof.CityLiveEvidenceActor", class_parents)
            old_module = actor["class_path"].split(".", 1)[0] == "/Script/CityMaterializationProof"
            if proof_class or actor["role"] in {"head_anchor", "resource_state"} or old_module:
                relevant.append(actor)
            if not proof_class:
                require(all(actor[key] is None for key in ("role", "domain", "record_raw_sha256", "generation", "allocation_owner")))
            if _inherits(actor["class_path"], "/Script/Engine.Pawn", class_parents):
                pawns.append(actor)
            if _inherits(actor["class_path"], "/Script/Engine.Controller", class_parents):
                controllers.append(actor)
    require(len(world_paths) == len(set(world_paths)) and len(actor_ids) == len(set(actor_ids)))
    games = [world for world in worlds if world["world_type"] == "Game"]
    selected = games[0] if len(games) == 1 else None
    wrong_world = (selected is None or selected["world_path"].split(".", 1)[0] != policy["runtime"]["map"]
                   or selected["game_mode_class"] != policy["runtime"]["game_mode"])
    if selected is not None:
        wrong_world = wrong_world or any(row["world_path"] != selected["world_path"] for row in relevant)
    anchors = [row for row in relevant if row["role"] == "head_anchor"]
    resources = [row for row in relevant if row["role"] == "resource_state"]

    def homogeneous(items, field):
        values = {row[field] for row in items}
        return next(iter(values)) if len(values) == 1 else None

    summary = {"selected_world_path": None if selected is None else selected["world_path"],
               "anchor_count": len(anchors), "resource_actor_count": len(resources),
               "all_proof_actor_ids": sorted(row["actor_id"] for row in relevant),
               "record_sha256": homogeneous(relevant, "record_raw_sha256"),
               "generation": homogeneous(relevant, "generation"),
               "allocation_owner": homogeneous(resources, "allocation_owner")}
    return {"rows": rows, "relevant": relevant, "anchors": anchors, "resources": resources,
            "pawns": pawns, "controllers": controllers, "wrong_world": wrong_world, "summary": summary}


def _representation_errors(facts, observation, record_raw, generation, owner, domain):
    """Return every violated physical predicate in the frozen precedence order."""
    rows = facts["relevant"]; errors = []
    if facts["wrong_world"]: errors.append("wrong_world")
    if any(row["generation"] != generation for row in rows): errors.append("generation")
    if (len(rows) != 2 or len(facts["anchors"]) != 1 or len(facts["resources"]) != 1
            or any(row["pending_kill"] or row["class_path"].split(".", 1)[0] == "/Script/CityMaterializationProof" for row in rows)):
        errors.append("cardinality")
    if any(row["domain"] != domain or row["record_raw_sha256"] != digest(record_raw) for row in rows):
        errors.append("record_domain")
    if (any(row["allocation_owner"] is not None for row in facts["anchors"])
            or any(row["allocation_owner"] != owner for row in facts["resources"])):
        errors.append("owner")
    if any(not same_json(observation[key], value) for key, value in facts["summary"].items()):
        errors.append("summary")
    return errors


def _startup_world(policy, startup, class_parents):
    startup = wire(policy, "startup", stored(startup))
    facts = _world_facts(policy, startup["worlds"], class_parents)
    require(not facts["wrong_world"] and not facts["relevant"] and not facts["pawns"])
    require(all(row["auto_receive_input"] == 0 for row in facts["rows"]))
    require(len(startup["controllers"]) == len(facts["controllers"]) == 1)
    controller = startup["controllers"][0]; actor = facts["controllers"][0]
    require(controller == {"actor_path": actor["actor_path"], "class_path": "/Script/Engine.PlayerController", "pawn_path": None})
    require(actor["class_path"] == controller["class_path"] and not actor["pending_kill"])
    return facts


def _child_world_fault_relations(policy, event, domain, binding, artifacts, class_parents):
    """Calculate the five frozen child fault effects from complete census rows."""
    event = wire(policy, 'fault_event', stored(event))
    name = event['failure_case']
    require(name in ('F13', 'F14', 'F15', 'F16a', 'F16b'))
    program = next(row for row in policy['failure_programs'] if row['id'] == name)
    require(program['domain'] == domain and event['consumed'] is True and
            all(event[key] == program[key] for key in ('executor', 'stage', 'action', 'underlying_code')))
    facts = []
    for side in ('before', 'after'):
        snapshot = event[side]
        require(snapshot['kind'] == 'world')
        observation = wire(policy, 'live_observation', stored(snapshot['observation']))
        require(all(observation[key] == binding[key] for key in ('witness_id', 'domain', 'launch_id')) and
                observation['binding_sha256'] == digest(stored(binding)) and observation['operation_id'] == 'materialize_0002')
        census = _world_facts(policy, observation['worlds'], class_parents)
        require(not census['wrong_world'] and all(same_json(observation[key], value) for key, value in census['summary'].items()))
        require(not census['pawns'] and all(row['auto_receive_input'] == 0 for row in census['rows']))
        facts.append(census)
    before, after = (event[side]['observation'] for side in ('before', 'after'))
    old, new = facts
    r0, r1 = artifacts['canonical/R0.json'], artifacts['canonical/R1.json']
    if name in ('F13', 'F14'):
        require(same_json(before, after) and not new['anchors'] and len(new['relevant']) == len(new['resources']) == 1)
        actor = new['resources'][0]
        require(actor['generation'] == 1 and actor['domain'] == domain and actor['record_raw_sha256'] == digest(r1) and
                actor['allocation_owner'] == 'domain_A' and not actor['pending_kill'])
    else:
        require(not _representation_errors(old, before, r1, 1, 'domain_A', domain))
        if name == 'F15':
            # Reconstruct the only permitted change; every other field and
            # every other Actor stays byte-equivalent under the wire law.
            expected = strict_json(stored(before))
            target = old['resources'][0]['actor_id']
            for world in expected['worlds']:
                for actor in world['actors']:
                    if actor['actor_id'] == target: actor['allocation_owner'] = 'domain_B'
            expected['allocation_owner'] = 'domain_B'
            require(same_json(after, expected))
        else:
            prior = {row['actor_id']: row for row in old['rows']}
            current = {row['actor_id']: row for row in new['rows']}
            extra = set(current) - set(prior)
            require(len(extra) == 1 and all(same_json(current.get(key), row) for key, row in prior.items()))
            actor = current[next(iter(extra))]
            generation = 1 if name == 'F16a' else 0
            require(actor in new['resources'] and actor['domain'] == domain and actor['generation'] == generation and
                    actor['record_raw_sha256'] == digest(r1 if generation else r0) and
                    actor['allocation_owner'] == ('domain_A' if generation else None) and not actor['pending_kill'])
            # UE may reuse a null array slot. Check full slot coverage through
            # _world_facts and preserve all world identity/configuration fields.
            def context(worlds):
                return [{key: value for key, value in world.items() if key not in
                         ('actors', 'actor_array_size', 'visited_slots', 'null_slots')} for world in worlds]
            require(same_json(context(before['worlds']), context(after['worlds'])))
        errors = _representation_errors(new, after, r1, 1, 'domain_A', domain)
        require(errors and errors[0] == {'F15': 'owner', 'F16a': 'cardinality', 'F16b': 'generation'}[name])
    return {'domain': domain, 'before': old, 'after': new, 'underlying_code': program['underlying_code']}


def _world_trace_relations(policy, artifacts, case, trace, canonical, class_parents):
    """Join actual census rows, receipts, emissions and head dispositions.

    Inputs must already pass raw reconciliation, scheduling, materialization
    bytes and canonical replay. The caller authenticates the native class graph
    and process/build identity. This predicate alone grants no live acceptance.
    """
    name = case['witness_id']
    require(name in policy['artifact_hash_graph']['case_ids'])
    bindings = {row['domain']: row for row in case['process_bindings']}
    r0, r1 = artifacts['canonical/R0.json'], artifacts['canonical/R1.json']
    initial = strict_json(r0)
    head = r0; represented = {}; receipts = {}; observations = {}; inspected = {}; effects = {}
    samples = {}; states = {}; head_rows = []; publication_classifications = set()
    process_dead = {'F07': 'domain_A', 'F08': 'domain_B', 'F11': 'domain_A', 'F12': 'domain_B'}.get(name)

    def receipt_actors(domain, facts):
        receipt = receipts[domain]['r1_representation']
        if receipt is not None:
            require(receipt['anchor_actor_id'] == facts['anchors'][0]['actor_id'] and
                    receipt['resource_actor_id'] == facts['resources'][0]['actor_id'])

    for event in trace['events']:
        kind, payload, domain = event['event_id'], event['payload'], event['domain']
        if kind == 'canonical_call' and payload['function'] == 'resolve_external_batch' and payload['exception_code'] is None:
            require(head == r0 and payload['published_record_raw_utf8'].encode() == r1)
            head = r1
        if kind == 'liveness' and payload['checkpoint'] == 'terminal':
            samples[domain] = payload
        if kind == 'head_event':
            row = wire(policy, 'head_event', stored(payload))
            require(row['canonical_raw_utf8'].encode() == head and row['canonical_role'] == ('R0' if head == r0 else 'R1'))
            edge = row['edge']; observation = None
            if edge in ('initialize', 'publish'):
                require(domain is None and row['domain'] is None)
                disposition = 'unclaimed'
                if edge == 'initialize': require(head == r0)
                else:
                    require(head == r1)
                    publication_classifications = set(bindings)
            elif edge == 'invalidate_claims':
                require(domain in bindings and head == r0)
                disposition = 'unclaimed'
            elif edge == 'classify':
                require(domain in represented)
                disposition = 'current' if represented[domain] == head else 'stale'
                if domain in publication_classifications:
                    require(disposition == 'stale')
                    publication_classifications.remove(domain)
                    if row['observation_sha256'] is not None: observation = observations[domain]
                else:
                    observation = observations[domain]
                    require((domain, observation['operation_id']) in inspected and inspected[(domain, observation['operation_id'])]['valid'])
            else:
                require(edge == 'terminal' and domain in samples)
                sample = samples[domain]
                dead = sample['poll_returncode'] is not None
                require(dead == (domain == process_dead) and (sample['observed_process'] is None) == dead)
                if dead:
                    require((domain, 'inspect_terminal') not in inspected)
                    disposition = 'unavailable'
                else:
                    observation = observations[domain]
                    require(observation['operation_id'] == 'inspect_terminal')
                    disposition = ('unavailable' if name in ('F13', 'F14') else 'unclaimed') if domain in effects else (
                        'stale' if head == r1 else 'unclaimed')
            require(row['domain'] == domain and row['disposition'] == disposition and row['observation_sha256'] == (
                    None if observation is None else digest(stored(observation))))
            if domain is not None: states[domain] = disposition
            head_rows.append(row)
        if kind != 'wire_event': continue
        wire_kind = payload['parsed_schema']
        message = wire(policy, wire_kind, payload['raw_line_utf8'].encode())
        if wire_kind == 'startup':
            _startup_world(policy, message, class_parents)
        elif wire_kind == 'fault_event':
            require(domain not in effects and message['failure_case'] == name)
            effects[domain] = _child_world_fault_relations(policy, message, domain, bindings[domain], artifacts, class_parents)
        elif wire_kind == 'response' and message['status'] == 'ok':
            operation = message['operation_id']; result = message['payload']
            if message['command'] == 'materialize':
                represented[domain] = r0 if operation == 'materialize_0001' else r1
                receipts[domain] = result
                if domain in effects: receipt_actors(domain, effects[domain]['before'])
            elif message['command'] == 'inspect':
                observation = wire(policy, 'live_observation', stored(result))
                require(all(observation[field] == message[field] for field in
                            ('witness_id', 'domain', 'launch_id', 'operation_id', 'binding_sha256')))
                facts = _world_facts(policy, observation['worlds'], class_parents)
                require(not facts['wrong_world'] and not facts['pawns'] and all(row['auto_receive_input'] == 0 for row in facts['rows']))
                require(all(same_json(observation[key], value) for key, value in facts['summary'].items()))
                if domain in effects:
                    effect = effects[domain]
                    require(same_json(facts['relevant'], effect['after']['relevant']))
                    errors = _representation_errors(facts, observation, r1, 1, 'domain_A', domain)
                    require(errors and errors[0] == {'F13': 'cardinality', 'F14': 'cardinality', 'F15': 'owner',
                                                    'F16a': 'cardinality', 'F16b': 'generation'}[name])
                else:
                    raw = represented[domain]
                    require(not _representation_errors(facts, observation, raw, 0 if raw == r0 else 1,
                                                       None if raw == r0 else 'domain_A', domain))
                    receipt_actors(domain, facts)
                observations[domain] = observation
                inspected[(domain, operation)] = {'facts': facts, 'valid': domain not in effects}
            elif message['command'] == 'emit':
                require(domain in observations and represented[domain] == r0)
                observed = inspected[(domain, observations[domain]['operation_id'])]
                require(observed['valid'])
                q_raw = artifacts['canonical/' + ('QA' if domain == 'domain_A' else 'QB') + '.json']
                q = canonical.external_evidence_q(initial, domain)
                require(canonical.stored_payload_bytes(q) == q_raw and result['q_raw_utf8'].encode() == q_raw)
                routing = {field: message[field] for field in ('witness_id', 'domain', 'launch_id', 'operation_id', 'binding_sha256')}
                fields = {'physical_event_id': q['physical_event_id'], 'interaction_counter': 1,
                          'q_raw_sha256': digest(q_raw), 'q_canonical_hash': canonical.q_hash(q)}
                physical = dict(routing, **fields, schema='city.live_evidence_physical_event.v1',
                                actor_id=observed['facts']['resources'][0]['actor_id'], accepted_record_raw_sha256=digest(r0))
                wrapper = dict(routing, **fields, schema='city.live_evidence_emission.v1', source_record_hash=canonical.canonical_hash(initial))
                require(same_json(result['physical_event'], physical) and same_json(result['wrapper'], wrapper))
                require(result['acceptance_receipt_raw_utf8'] == receipts[domain]['r0_acceptance_raw_utf8'])
                raw = result['emission_receipt_raw_utf8'].encode()
                receipt = strict_json(raw)
                require(canonical.stored_receipt_bytes(receipt) == raw == canonical.stored_receipt_bytes(
                    canonical.evidence_emission_receipt(initial, q, domain, bindings[domain]['launch_id'])))
    require(not publication_classifications and set(states) == set(bindings))
    if name.startswith('W'):
        require(head == r1 and set(states.values()) == {'current'} and set(represented.values()) == {r1})
    return {'terminal_dispositions': states, 'head_events': head_rows,
            'observed_operations': sorted([list(key) for key in inspected]), 'child_effects': sorted(effects)}


def _harness_fault_relations(policy, artifacts, case, trace, canonical):
    """Join harness fault snapshots to independently checked calls and samples.

    Call after raw/schedule/canonical/materialization/liveness/world predicates.
    Source authentication still establishes execution of the acquisition code;
    matching snapshot objects alone cannot prove a kernel call or live fault.
    """
    name = case['witness_id']
    require(name in policy['artifact_hash_graph']['case_ids'])
    program = next((row for row in policy['failure_programs'] if row['id'] == name), None)
    faults = [row for row in trace['events'] if row['event_id'] == 'fault_event']
    if program is None or program['executor'] != 'harness':
        require(not faults)
        return None
    require(len(faults) == 1)
    event = faults[0]; fault = wire(policy, 'fault_event', stored(event['payload']))
    domain = program['domain']
    require(event['domain'] == domain and fault['failure_case'] == name and fault['consumed'] is True and
            all(fault[key] == program[key] for key in ('executor', 'stage', 'action', 'underlying_code')))
    binding = next(row for row in case['process_bindings'] if row['domain'] == domain)

    def bytes_state(side, semantic_type, expected):
        state = fault[side]
        require(state['kind'] == 'bytes' and state['semantic_type'] == semantic_type and
                _base64(state['raw_base64']) == expected)

    if program['underlying_code'].startswith('concurrent_external_'):
        calls = [row for row in trace['events'] if row['event_id'] == 'canonical_call']
        require(calls and calls[-1]['payload']['exception_code'] == program['underlying_code'])
        call = calls[-1]['payload']; after = call['arguments']
        before = strict_json(stored(after))
        if call['function'] == 'admit_external_input_candidate':
            capture = next(row['emission'] for row in case['captured_evidence'] if row['domain'] == domain)
            require(capture is not None)
            before['q_object_raw_utf8'] = capture['q_raw_utf8']
            before['q_raw_base64'] = base64.b64encode(capture['q_raw_utf8'].encode()).decode('ascii')
            semantic_type = 'admission_arguments'
        else:
            require(call['function'] == 'construct_bext_from_sealed_fixture_set')
            semantic_type = 'construction_arguments'
            if name != 'F01':
                admitted = {row['domain']: row['payload']['return_raw_utf8'] for row in calls
                            if row['payload']['function'] == 'admit_external_input_candidate' and row['payload']['exception_code'] is None}
                require(set(admitted) == {'domain_A', 'domain_B'})
                before['presentation_members_raw_utf8'] = [admitted[peer] for peer in ('domain_A', 'domain_B')]
        require(event['operation_id'] is None)
        bytes_state('before', semantic_type, stored(before))
        bytes_state('after', semantic_type, stored(after))
    elif name in ('F09', 'F17', 'F18'):
        commands = [row for row in trace['events'] if row['event_id'] == 'wire_event' and row['domain'] == domain and
                    row['operation_id'] == 'materialize_0002' and row['payload']['parsed_schema'] == 'command']
        require(len(commands) == 1 and event['operation_id'] == 'materialize_0002')
        raw = artifacts['canonical/R1.json']; successor = strict_json(raw)
        routing = {field: binding[field] for field in ('witness_id', 'domain', 'launch_id')}
        routing.update(operation_id='materialize_0002', binding_sha256=digest(stored(binding)))
        projection = dict(routing, schema='city.live_evidence_projection.v1', record_role='R1', generation=1,
                          record_raw_sha256=digest(raw), record_canonical_hash=canonical.canonical_hash(successor),
                          allocation_owner=successor['current_causal_state']['shared_slot']['allocation_owner'])
        before = dict(routing, schema='city.live_evidence_command.v1', command='materialize',
                      payload={'projection': projection, 'record_raw_utf8': raw.decode(), 'launch_receipt_raw_utf8': None})
        bytes_state('before', 'materialize_command', stored(before))
        bytes_state('after', 'materialize_command', commands[0]['payload']['raw_line_utf8'].encode())
    else:
        require(name in ('F07', 'F08', 'F11', 'F12') and event['operation_id'] is None)
        require(fault['before']['kind'] == fault['after']['kind'] == 'process')
        before = wire(policy, 'liveness', stored(fault['before']['sample']))
        after = wire(policy, 'liveness', stored(fault['after']['sample']))
        require(before['checkpoint'] == after['checkpoint'] == 'terminal' and
                before['domain'] == after['domain'] == domain and before['launch_id'] == binding['launch_id'] and
                before['poll_returncode'] is None and before['observed_process'] is not None)
        samples = [row['payload'] for row in trace['events'] if row['event_id'] == 'liveness' and row['domain'] == domain]
        startup = next(row for row in samples if row['checkpoint'] == 'startup' and row['launch_id'] == binding['launch_id'])
        terminal = next(row for row in samples if row['checkpoint'] == 'terminal' and row['launch_id'] == binding['launch_id'])
        _liveness_series_relations(policy, [startup, before])
        require(terminal['poll_returncode'] is not None and terminal['observed_process'] is None)
        if name != 'F07':
            _liveness_series_relations(policy, [startup, after])
            require(same_json(after, terminal))
        else:
            require(after['launch_id'] != binding['launch_id'] and after['poll_returncode'] is None and after['observed_process'] is not None)
            replacement = after['observed_process']
            require((replacement['pid'], replacement['macos_birth_tuple']) != (binding['pid'], binding['macos_birth_tuple']))
            cleanup = next(row for row in samples if row['checkpoint'] == 'cleanup' and row['launch_id'] == after['launch_id'])
            _liveness_series_relations(policy, [after, cleanup], initial_checkpoint='terminal')
    return program['underlying_code']


def _case_outcome_relations(policy, artifacts, case, trace):
    """Recompute the case envelope after every protocol predicate has passed.

    Raw errors are usable here only because canonical replay and physical/process
    fault predicates have already checked them. This is not a stand-alone oracle
    for the authenticity of those records or for release acceptance.
    """
    case = wire(policy, 'case_record', stored(case))
    name = case['witness_id']
    require(name in policy['artifact_hash_graph']['case_ids'])
    witnesses = {row['id'] for row in policy['witnesses']}
    programs = {row['id']: row for row in policy['failure_programs']}
    canonical_faults = {'C%02d' % (number + 1): policy['canonical_fault_codes'][point]
                        for number, point in enumerate(policy['canonical_faults'])}
    publications = []; codes = set(); dispositions = {}; cleanup = []
    for event in trace['events']:
        kind, payload = event['event_id'], event['payload']
        if kind == 'canonical_call':
            if payload['exception_code'] is not None: codes.add(payload['exception_code'])
            if payload['published_record_raw_utf8'] is not None:
                require(payload['function'] == 'resolve_external_batch' and payload['exception_code'] is None)
                publications.append(payload['published_record_raw_utf8'].encode())
        elif kind == 'fault_event':
            codes.add(payload['underlying_code'])
        elif kind == 'wire_event':
            message = wire(policy, payload['parsed_schema'], payload['raw_line_utf8'].encode())
            if payload['parsed_schema'] == 'response' and message['status'] == 'error': codes.add(message['error']['underlying_code'])
            elif payload['parsed_schema'] == 'fault_event': codes.add(message['underlying_code'])
        elif kind == 'head_event' and payload['domain'] is not None:
            dispositions[payload['domain']] = payload['disposition']
        elif kind == 'liveness' and payload['checkpoint'] == 'cleanup':
            cleanup.append(payload)
    require(set(dispositions) == {'domain_A', 'domain_B'} and len(publications) <= 1 and None not in codes)
    published = bool(publications)
    require(not published or publications[0] == artifacts['canonical/R1.json'])
    initial = artifacts['canonical/R0.json'].decode()
    terminal = artifacts['canonical/R1.json'].decode() if published else initial
    require(case['canonical_artifacts'] == {'initial_raw_utf8': initial,
                'published_raw_utf8': terminal if published else None, 'terminal_raw_utf8': terminal})
    identities = {(row['domain'], row['launch_id']) for row in cleanup}
    require(len(identities) == len(cleanup) and identities == set(trace['startups']) and
            all(row['poll_returncode'] is not None and row['observed_process'] is None for row in cleanup))
    synchronized = published and not codes and set(dispositions.values()) == {'current'}
    if name in witnesses:
        require(synchronized)
        status, failure_codes = 'accepted', []
    else:
        require(not synchronized and all(value != 'current' for value in dispositions.values()))
        expected = canonical_faults[name] if name in canonical_faults else programs[name]['underlying_code']
        require(codes == {expected})
        status = 'expected_failure'
        if name in canonical_faults: failure_codes = [expected]
        else:
            families = [row for row in policy['failure_cases'] if name in row['runs']]
            require(len(families) == 1)
            failure_codes = [families[0]['failure_code']]
    claims = {'synchronized_representation': synchronized, 'canonical_commit': published,
              'production_ready': False, 'trusted_ci': False, 'game_sealed': False}
    require(case['status'] == status and case['failure_codes'] == failure_codes and same_json(case['claims'], claims))
    return {'status': status, 'failure_codes': failure_codes, 'claims': claims}


def _launch_input_relations(policy, startup_raw, observation, build, source_bytes, process_root, operator_user):
    """Join a checked process observation to the supplied executed-build inputs.

    Build execution, external byte authentication and source effects must be
    verified independently. Agreement between these records cannot prove them.
    This also checks the F07 replacement, which never receives a binding.
    """
    startup = wire(policy, 'startup', startup_raw)
    process = wire(policy, 'process_observation', stored(observation))
    build = wire(policy, 'build_record', stored(build))
    require(type(source_bytes) is dict and type(process_root) is str and type(operator_user) is str and operator_user)
    base = '/Users/boandersson/Projects/CITY'
    root = Path(process_root)
    require(root.is_absolute() and str(root) == process_root and '..' not in root.parts)
    project = build['project']
    require(project['realpath'] == base + '/' + policy['runtime']['project'])
    raw = source_bytes[policy['runtime']['project']]
    require(type(raw) is bytes and digest(raw) == project['sha256'] == policy['unchanged_dependencies'][policy['runtime']['project']]
            and len(raw) == project['size_bytes'])
    require(build['returncode'] == 0 and build['cwd'] == base and build['argv'] == [
        value.format(absolute_city_project=project['realpath']) for value in policy['build_argv']])
    values = dict(engine=policy['runtime']['engine'], absolute_city_project=project['realpath'],
                  absolute_domain_root=process_root, observed_operator_user=operator_user,
                  witness_id=startup['witness_id'], domain=startup['domain'], launch_id=startup['launch_id'])
    require(process['pid'] == startup['pid'] and process['pid'] > 0 and process['ppid'] > 0 and
            process['cwd_realpath'] == startup['cwd_realpath'] == base and same_json(process['startup'], startup))
    require(process['argv'] == [value.format_map(values) for value in policy['launch_argv']] and
            process['environment'] == {key: value.format_map(values) for key, value in policy['launch_environment'].items()})
    require(process['executable'] == build['editor'] and build['editor']['realpath'] == policy['runtime']['engine'])
    external = build['external_inputs']
    for rows in (build['modules'], external['build_inputs'], external['engine_configs'], external['engine_plugins'], external['loaded_images']):
        paths = [row['realpath'] for row in rows]
        require(paths and paths == sorted(set(paths)) and all(Path(path).is_absolute() and
                str(Path(path)) == path and '..' not in Path(path).parts for path in paths))
    require(startup['config_files'] == external['engine_configs'] and startup['enabled_plugins'] == external['engine_plugins'] and
            startup['loaded_images'] == process['loaded_images'] == external['loaded_images'])
    images = {row['realpath']: row for row in external['loaded_images']}
    require(build['editor']['realpath'] in images and images[build['editor']['realpath']]['sha256'] == build['editor']['sha256'] and
            images[build['editor']['realpath']]['architecture'] == 'arm64' and
            all(row['architecture'] in ('arm64', 'arm64e') for row in images.values()) and
            all(row['architecture'] == 'arm64' and row in external['loaded_images'] for row in build['modules']))
    module = startup['proof_module']
    require(module['realpath'] == base + '/' + policy['runtime']['plugin'] + '/Binaries/Mac/libUnrealEditor-CityLiveEvidenceProof.dylib' and
            module['source'] == 'dyld' and module in build['modules'])
    # Frozen project configuration and the new plugin descriptor must occur in
    # the actual startup inventory with their authenticated source bytes.
    configs = {row['realpath']: row for row in external['engine_configs']}
    plugins = {row['realpath']: row for row in external['engine_plugins']}
    config_prefix = str(Path(policy['runtime']['project']).parent) + '/Config/'
    required_configs = {name for name in policy['unchanged_dependencies'] if name.startswith(config_prefix)}
    require(required_configs and {path for path in configs if path.startswith(base + '/' + config_prefix)} ==
            {base + '/' + name for name in required_configs})
    for name in sorted(required_configs | {policy['runtime']['plugin'] + '/CityLiveEvidenceProof.uplugin'}):
        row = (configs if name in required_configs else plugins).get(base + '/' + name)
        raw = source_bytes[name]
        require(row is not None and type(raw) is bytes and row['sha256'] == digest(raw) and row['size_bytes'] == len(raw))
        if name in required_configs: require(digest(raw) == policy['unchanged_dependencies'][name])
    return {'witness_id': startup['witness_id'], 'domain': startup['domain'], 'launch_id': startup['launch_id'],
            'pid': process['pid'], 'ppid': process['ppid'], 'macos_birth_tuple': process['macos_birth_tuple'],
            'process_root_realpath': process_root, 'operator_user': operator_user}


def _case_launch_relations(policy, case, trace, build, source_bytes, class_parents):
    """Join startup bytes, original bindings and every launched input inventory.

    Raw reconciliation and the complete liveness predicate run first. Fresh
    directory creation and external/native authentication remain outer gates.
    """
    bindings = {(row['domain'], row['launch_id']): row for row in case['process_bindings']}
    require(len(bindings) == 2 and {key[0] for key in bindings} == {'domain_A', 'domain_B'})
    starts = {}; observations = {}
    for event in trace['events']:
        payload = event['payload']
        if event['event_id'] == 'wire_event' and payload['parsed_schema'] == 'startup':
            raw = payload['raw_line_utf8'].encode()
            startup = wire(policy, 'startup', raw)
            key = (startup['domain'], startup['launch_id'])
            require(key not in starts and startup['witness_id'] == case['witness_id'])
            starts[key] = raw
        elif event['event_id'] == 'liveness' and payload['checkpoint'] == 'startup':
            key = (payload['domain'], payload['launch_id'])
            require(key in bindings and key not in observations and payload['observed_process'] is not None)
            observations[key] = payload['observed_process']
        elif event['event_id'] == 'fault_event' and payload['failure_case'] == 'F07':
            require(case['witness_id'] == 'F07' and payload['after']['kind'] == 'process')
            sample = payload['after']['sample']; key = (sample['domain'], sample['launch_id'])
            require(key not in observations and key not in bindings and key[0] == 'domain_A' and sample['observed_process'] is not None)
            observations[key] = sample['observed_process']
    require(set(starts) == set(observations) and set(bindings) <= set(starts) and
            len(starts) == (3 if case['witness_id'] == 'F07' else 2))
    identities = []; roots = []; parent = None; operator = None
    for key in sorted(starts):
        process = wire(policy, 'process_observation', stored(observations[key]))
        environment = process['environment']
        home = environment.get('HOME')
        require(type(home) is str and home.endswith('/home'))
        root = home[:-5]; user = environment.get('USER')
        identity = _launch_input_relations(policy, starts[key], process, build, source_bytes, root, user)
        require(identity['domain'] == key[0] and identity['launch_id'] == key[1])
        require((parent is None or parent == identity['ppid']) and (operator is None or operator == user))
        parent, operator = identity['ppid'], user
        current = Path(root)
        require(all(current != other and current not in other.parents and other not in current.parents for other in roots))
        roots.append(current)
        if key in bindings:
            require(bindings[key]['process_root_realpath'] == root)
            _binding_relations(policy, bindings[key], starts[key], process, build['project'], root, user, class_parents)
        else:
            _startup_world(policy, process['startup'], class_parents)
        identities.append(identity)
    require(len({row['launch_id'] for row in identities}) == len(identities))
    return identities


def _case_protocol_relations(policy, artifacts, case, canonical, class_parents, build=None, source_bytes=None):
    """Execute the complete case-record predicates in dependency order.

    The outer verifier still must authenticate release bytes, source/build and
    native class/launch inputs, including each initial binding. This entrypoint
    does not replace those gates or accept a release by itself.
    """
    trace = _trace_relations(policy, artifacts, case)
    _operation_schedule_relations(policy, case, trace)
    _liveness_trace_relations(policy, case, trace)
    # Missing outer inputs fail at this join. Internal component callers may
    # stop earlier on a raw/liveness defect, but can never skip the build join.
    launches = _case_launch_relations(policy, case, trace, build, source_bytes, class_parents)
    _replay_canonical(policy, artifacts, case, canonical)
    _materialization_relations(policy, artifacts, case, trace, canonical)
    _world_trace_relations(policy, artifacts, case, trace, canonical, class_parents)
    _harness_fault_relations(policy, artifacts, case, trace, canonical)
    outcome = _case_outcome_relations(policy, artifacts, case, trace)
    return {'outcome': outcome, 'launches': launches}


def _acquisition_relations(policy, artifacts, case_results):
    """Reconcile the full acquisition after independently checking every case.

    case_results must come from _case_protocol_relations, never release-supplied
    booleans. This joins their calculations; it does not authenticate execution,
    current Git identity, fresh directory ownership or external/native bytes.
    """
    graph = policy['artifact_hash_graph']
    names = graph['case_ids']
    require(type(case_results) is dict and list(case_results) == names)
    acquisition = wire(policy, 'acquisition_record', artifacts['acquisition.json'])
    build = wire(policy, 'build_record', artifacts['build.json'])
    require(acquisition['artifact_members'] == policy['artifact_relative_paths'])
    check_index(acquisition['artifact_hashes'], graph['acquisition_targets'], artifacts)
    require(acquisition['build_sha256'] == digest(artifacts['build.json']))
    require([row['witness_id'] for row in acquisition['cases']] == names)
    for field in ('source_commit', 'source_tree'):
        require(re.fullmatch('[0-9a-f]{40}', acquisition[field]) is not None and acquisition[field] == build[field])
    witnesses = {row['id'] for row in policy['witnesses']}
    programs = {row['id']: row for row in policy['failure_programs']}
    canonical_faults = {'C%02d' % (number + 1): policy['canonical_fault_codes'][point]
                        for number, point in enumerate(policy['canonical_faults'])}
    all_launches = []; roots = []; launch_ids = set(); process_ids = set(); parents = set(); users = set()
    synchronized = []; publications = []
    identity_fields = {'witness_id', 'domain', 'launch_id', 'pid', 'ppid', 'macos_birth_tuple', 'process_root_realpath', 'operator_user'}
    birth_schema = policy['wire_schemas']['process_observation']['properties']['macos_birth_tuple']
    for entry in acquisition['cases']:
        name = entry['witness_id']; path = name + '/record.json'
        require(entry['record_path'] == path and entry['record_sha256'] == digest(artifacts[path]))
        case = wire(policy, 'case_record', artifacts[path])
        require(case['witness_id'] == name)
        result = case_results[name]
        require(type(result) is dict and set(result) == {'outcome', 'launches'})
        outcome = result['outcome']
        require(type(outcome) is dict and set(outcome) == {'status', 'failure_codes', 'claims'} and
                same_json(outcome, {key: case[key] for key in outcome}))
        is_witness = name in witnesses
        published = is_witness or (name in programs and programs[name]['prefix'] in ('P3', 'P4', 'P5'))
        if is_witness:
            failure_codes = []
        elif name in canonical_faults:
            failure_codes = [canonical_faults[name]]
        else:
            families = [family for family in policy['failure_cases'] if name in family['runs']]
            require(len(families) == 1)
            failure_codes = [families[0]['failure_code']]
        claims = {'synchronized_representation': is_witness, 'canonical_commit': published,
                  'production_ready': False, 'trusted_ci': False, 'game_sealed': False}
        require(outcome['status'] == ('accepted' if is_witness else 'expected_failure') and
                outcome['failure_codes'] == failure_codes and same_json(outcome['claims'], claims))
        if is_witness: synchronized.append(name)
        if published: publications.append(name)
        rows = result['launches']
        require(type(rows) is list and len(rows) == (3 if name == 'F07' else 2))
        bindings = {(row['domain'], row['launch_id']): row for row in case['process_bindings']}
        require(len(bindings) == len(case['process_bindings']) == 2 and {key[0] for key in bindings} == {'domain_A', 'domain_B'})
        keys = set()
        for row in rows:
            require(type(row) is dict and set(row) == identity_fields and row['witness_id'] == name and
                    row['domain'] in ('domain_A', 'domain_B') and type(row['launch_id']) is str and row['launch_id'] and
                    type(row['operator_user']) is str and row['operator_user'] and type(row['pid']) is int and row['pid'] > 0 and
                    type(row['ppid']) is int and row['ppid'] > 0 and
                    schema_accepts(policy['wire_schemas'], birth_schema, row['macos_birth_tuple']))
            key = (row['domain'], row['launch_id'])
            require(key not in keys and row['launch_id'] not in launch_ids)
            keys.add(key); launch_ids.add(row['launch_id'])
            birth = row['macos_birth_tuple']
            identity = (row['pid'], birth['seconds'], birth['microseconds'])
            # PIDs may be reused after exit. The exact PID/birth identity may
            # never be shared by two launches in this acquisition.
            require(identity not in process_ids)
            process_ids.add(identity); parents.add(row['ppid']); users.add(row['operator_user'])
            require(type(row['process_root_realpath']) is str)
            root = Path(row['process_root_realpath'])
            require(root.is_absolute() and str(root) == row['process_root_realpath'] and '..' not in root.parts and
                    all(root != other and root not in other.parents and other not in root.parents for other in roots))
            roots.append(root)
            if key in bindings:
                binding = bindings[key]
                require(binding['witness_id'] == name and binding['pid'] == row['pid'] and
                        same_json(binding['macos_birth_tuple'], birth) and binding['process_root_realpath'] == str(root))
            all_launches.append(row)
        require(set(bindings) <= keys and (not (keys - set(bindings)) if name != 'F07' else
                len(keys - set(bindings)) == 1 and next(iter(keys - set(bindings)))[0] == 'domain_A'))
    require(len(all_launches) == policy['cost']['total_original_process_launches'] + policy['cost']['replacement_process_launches'] == 71 and
            len(parents) == len(users) == 1)
    claims = {'synchronized_representation': True, 'canonical_commit': True,
              'production_ready': False, 'trusted_ci': False, 'game_sealed': False}
    require(acquisition['status'] == 'complete' and same_json(acquisition['claims'], claims))
    return {'case_ids': list(names), 'synchronized_cases': synchronized, 'publication_cases': publications,
            'launches': all_launches, 'claims': claims,
            'source_commit': acquisition['source_commit'], 'source_tree': acquisition['source_tree']}


def _release_protocol_relations(context, canonical):
    """Execute every case and the acquisition join from authenticated raw bytes.

    The caller still owes current-source audit, executed build/external/native
    authentication and fresh-root proof. Public release acceptance stays closed
    until those gates execute. A caller cannot submit per-case success flags.
    """
    policy, artifacts = context['policy'], context['artifacts']
    build = wire(policy, 'build_record', artifacts['build.json'])
    # Reject disconnected recorded processes before consuming large external
    # image files. Supplied aggregate flags or class maps have no authority.
    for name in policy['artifact_hash_graph']['case_ids']:
        case = wire(policy, 'case_record', artifacts[name + '/record.json'])
        require(case['witness_id'] == name)
        trace = _trace_relations(policy, artifacts, case)
        _operation_schedule_relations(policy, case, trace)
        _liveness_trace_relations(policy, case, trace)
    _source_identity_relations(context)
    files = _build_file_relations(policy, artifacts['build.json'])
    _build_python_relations(policy, artifacts['build.json'], artifacts['build.log'], files)
    _build_action_relations(policy, artifacts['build.json'], artifacts['build.log'], files)
    image_result = _build_file_image_relations(policy, artifacts['build.json'], files)
    _build_cache_relations(policy, artifacts['build.json'], files, image_result)
    registry = _build_native_class_relations(policy, artifacts['build.json'], files)
    results = {}
    for name in policy['artifact_hash_graph']['case_ids']:
        case = wire(policy, 'case_record', artifacts[name + '/record.json'])
        results[name] = _case_protocol_relations(policy, artifacts, case, canonical, registry.class_parents,
                                                build, context['source_bytes'])
    return _acquisition_relations(policy, artifacts, results)


class NativeUbtArchive:
    """Data-only UE 5.8 TargetMakefile v37 action-section reader.

    Decode the installed engine's binary format here, without importing the
    candidate producer. The trailing UHT/cache section stays opaque. Neither
    command strings nor serializer names are executable authority.
    """

    def __init__(self, raw):
        require(type(raw) is bytes, 'lcer.build_action_graph_invalid')
        self.raw, self.offset, self.references = raw, 0, []

    def take(self, count):
        require(type(count) is int and 0 <= count <= len(self.raw) - self.offset,
                'lcer.build_action_graph_invalid')
        start = self.offset
        self.offset += count
        return self.raw[start:self.offset]

    def number(self, kind='i'):
        sizes = {'i': 4, 'I': 4, 'q': 8, 'd': 8, 'B': 1}
        require(kind in sizes, 'lcer.build_action_graph_invalid')
        return struct.unpack('<' + kind, self.take(sizes[kind]))[0]

    def boolean(self):
        value = self.number('B')
        require(value in (0, 1), 'lcer.build_action_graph_invalid')
        return bool(value)

    def string(self):
        size = self.number()
        if size == -1:
            return None
        try:
            value = self.take(size).decode('utf-8', 'strict')
        except UnicodeError as error:
            raise ValueError('lcer.build_action_graph_invalid') from error
        require('\0' not in value, 'lcer.build_action_graph_invalid')
        return value

    def reference(self, kind):
        index = self.number()
        if index == -1:
            return None
        require(0 <= index <= len(self.references), 'lcer.build_action_graph_invalid')
        if index == len(self.references):
            value = self.string()
            require(value is not None, 'lcer.build_action_graph_invalid')
            self.references.append((kind, value))
        observed, value = self.references[index]
        require(observed == kind, 'lcer.build_action_graph_invalid')
        return value

    def sequence(self, kind):
        count = self.number()
        if count == -1:
            return None
        require(0 <= count <= len(self.raw) - self.offset, 'lcer.build_action_graph_invalid')
        values = []
        for _ in range(count):
            if kind == 'string':
                value = self.string()
            elif kind in ('file', 'directory'):
                value = self.reference(kind)
            elif kind == 'config':
                value = {'key': [self.number(), self.string(), self.string(), self.string(), self.string()],
                         'values': self.sequence('string')}
            elif kind == 'target':
                value = [self.string(), self.string(), self.string(), self.sequence('string'),
                         self.string(), self.sequence('string'), self.string()]
            elif kind == 'log':
                value = digest(self.take(self.number()))
            elif kind == 'action':
                value = self.action()
            elif kind == 'root_name':
                value = [self.number(), self.string()]
            elif kind == 'root_directory':
                value = [self.number(), self.reference('directory')]
            elif kind == 'root_extra':
                value = [self.string(), self.reference('directory')]
            else:
                raise ValueError('lcer.build_action_graph_invalid')
            values.append(value)
        return values

    def action(self):
        serializer = self.reference('serializer')
        require(serializer in ('DefaultActionSerializer', 'ClangSpecificFileActionSerializer'),
                'lcer.build_action_serializer_unclassified')
        value = {'serializer': serializer, 'type': self.number('B'), 'artifact_mode': self.number('B')}
        for key in ('cwd', 'command', 'arguments'):
            value[key] = self.string()
        value['response_contents'] = self.sequence('string')
        for key in ('version', 'description', 'status'):
            value[key] = self.string()
        value['flags'] = [self.boolean() for _ in range(11)]
        for key in ('prerequisites', 'produced', 'deleted'):
            value[key] = self.sequence('file')
        value['root_names'] = self.sequence('root_name')
        value['root_directories'] = self.sequence('root_directory')
        value['root_extras'] = self.sequence('root_extra')
        value['root_use_vfs'] = self.boolean()
        value['dependency_list'] = self.reference('file')
        value['use_history'], value['high_priority'] = self.boolean(), self.boolean()
        value['weight'], value['cache_bucket'] = self.number('d'), self.number('I')
        if serializer == 'ClangSpecificFileActionSerializer':
            value['specific_file_source_directory'] = self.reference('directory')
            value['specific_file_output_directory'] = self.reference('directory')
            value['specific_file_response_lines'] = self.sequence('string')
        require(all(type(value[key]) is str for key in ('arguments', 'description', 'status', 'version'))
                and math.isfinite(value['weight']), 'lcer.build_action_graph_invalid')
        paths = [value['cwd'], value['command']]
        for key in ('prerequisites', 'produced', 'deleted'):
            require(type(value[key]) is list and len(set(value[key])) == len(value[key]),
                    'lcer.build_action_graph_invalid')
            paths.extend(value[key])
        if value['dependency_list'] is not None:
            paths.append(value['dependency_list'])
        require(all(type(path) is str and path.startswith('/') for path in paths),
                'lcer.build_action_graph_invalid')
        return value

    def decode(self):
        require(self.offset == 0 and self.number() == 37 and not self.boolean(),
                'lcer.build_action_graph_invalid')
        value = {'version': 37, 'created_ticks': self.number('q'), 'diagnostics': self.sequence('string'),
                 'external_metadata': self.string()}
        for key in ('executable', 'receipt', 'intermediate', 'intermediate_no_arch'):
            value[key] = self.string()
        value['target_type'], value['test_target'] = self.number(), self.boolean()
        value['config_dependencies'], value['deploy'] = self.sequence('config'), self.boolean()
        value['plugin_argument_script_lists'] = [self.sequence('string') for _ in range(6)]
        value['prebuild_targets'], value['log_bytes_sha256'] = self.sequence('target'), self.sequence('log')
        value['actions'] = self.sequence('action')
        require(value['actions'], 'lcer.build_action_graph_invalid')
        value['action_section_end_offset'], value['archive_sha256'] = self.offset, digest(self.raw)
        return value


def native_ubt_arguments(raw):
    """Recognize emitted double-quoted response tokens; never shell-expand."""
    require(type(raw) is bytes, 'lcer.build_response_invalid')
    try:
        text = raw.decode('utf-8', 'strict')
    except UnicodeError as error:
        raise ValueError('lcer.build_response_invalid') from error
    require(not any(c in text for c in ('\0', '\\', "'", '\ufeff')), 'lcer.build_response_invalid')
    tokens, cursor = [], 0
    while cursor < len(text):
        if text[cursor] in ' \t\r\n':
            cursor += 1
            continue
        match = re.match(r'(?:[^ \t\r\n"]+|"[^"]*")+', text[cursor:])
        require(match is not None, 'lcer.build_response_invalid')
        token = match[0].replace('"', '')
        cursor += len(match[0])
        require(cursor == len(text) or text[cursor] in ' \t\r\n', 'lcer.build_response_invalid')
        if token.startswith('@'):
            previous = tokens[-1] if tokens else None
            require((previous == '-rpath' and token.startswith(('@loader_path/', '@executable_path/')))
                    or (previous == '-install_name' and re.fullmatch(r'@rpath/[A-Za-z0-9_.-]+\.dylib', token)),
                    'lcer.build_response_invalid')
        tokens.append(token)
    return tokens


def native_clang_dependencies(raw):
    """Decode one emitted Make dependency rule without evaluating Make."""
    require(type(raw) is bytes, 'lcer.build_dependencies_invalid')
    try:
        text = raw.decode('utf-8', 'strict')
    except UnicodeError as error:
        raise ValueError('lcer.build_dependencies_invalid') from error
    require('\0' not in text and '#' not in text, 'lcer.build_dependencies_invalid')
    sides, word, cursor = [[]], '', 0
    while cursor < len(text):
        match = re.match(r'\\\n|\\[^\n]|\$\$|[ \t\r\n]+|:|[^\\$ \t\r\n:#]+', text[cursor:])
        require(match is not None, 'lcer.build_dependencies_invalid')
        part = match[0]
        cursor += len(part)
        if part == ':' or part == '\\\n' or part[0] in ' \t\r\n':
            if word:
                sides[-1].append(word)
                word = ''
            if part == ':':
                require(len(sides) == 1, 'lcer.build_dependencies_invalid')
                sides.append([])
        else:
            word += part[1:] if part.startswith('\\') or part == '$$' else part
    if word:
        sides[-1].append(word)
    require(len(sides) == 2 and all(sides), 'lcer.build_dependencies_invalid')
    return sides


def native_ubt_action_closure(archive, log_raw):
    """Derive receipt dependencies and the log's executed subset independently.

    A complete incremental build can print no action rows. The closure still
    contains every producing action. A matching log alone proves no invocation.
    """
    actions, producers = archive['actions'], {}
    for index, action in enumerate(actions):
        for path in action['produced']:
            require(path not in producers, 'lcer.build_action_graph_invalid')
            producers[path] = index
    require(archive['receipt'] in producers, 'lcer.build_action_graph_invalid')
    pending = [(producers[archive['receipt']], False)]
    active, selected = set(), set()
    while pending:
        index, finish = pending.pop()
        if finish:
            active.remove(index)
            selected.add(index)
        elif index not in selected:
            require(index not in active, 'lcer.build_action_graph_invalid')
            active.add(index)
            pending.append((index, True))
            pending.extend((producers[path], False) for path in actions[index]['prerequisites'] if path in producers)
    try:
        lines = log_raw.decode('utf-8', 'strict').splitlines()
    except (AttributeError, UnicodeError) as error:
        raise ValueError('lcer.build_execution_log_invalid') from error
    available, no_uba = {}, set()
    for index in selected:
        action = actions[index]
        label = action['description'] + ' ' + action['status']
        available[label] = available.get(label, 0) + 1
        if not action['flags'][3]:
            no_uba.add(label)
    rows = []
    for line in lines:
        match = re.fullmatch(r'\[([0-9]+)/([0-9]+)\] (.+)', line)
        require(match is not None or re.match(r'^\[\d', line) is None, 'lcer.build_execution_log_invalid')
        if match is not None:
            label = match[3]
            if label.endswith(' [NoUba]'):
                label = label[:-8]
                require(label in no_uba, 'lcer.build_execution_log_invalid')
            require(available.get(label, 0) > 0, 'lcer.build_execution_log_invalid')
            available[label] -= 1
            rows.append([int(match[1]), int(match[2])])
    require([line for line in lines if line.startswith('Result:')] == ['Result: Succeeded'],
            'lcer.build_execution_log_invalid')
    if rows:
        require(all(row[1] == len(rows) for row in rows)
                and sorted(row[0] for row in rows) == list(range(1, len(rows) + 1)),
                'lcer.build_execution_log_invalid')
    return {'action_indices': sorted(selected), 'executed_action_count': len(rows)}


class ExternalFileSnapshot:
    """Authenticate declared ordinary files directly from current disk bytes.

    This closes file-identity reads only. It cannot establish inventory
    completeness, build execution, input effects, or loaded-image identity.
    Readers use the recorded digest again when consuming bytes. No candidate
    harness or external program supplies the verification result.
    """

    def __init__(self, records):
        require(type(records) is list and records, 'lcer.external_input_invalid')
        self._records = {}
        for row in records:
            require(type(row) is dict and set(row) == {'realpath', 'sha256', 'size_bytes'}
                    and type(row['realpath']) is str and row['realpath']
                    and '\0' not in row['realpath'] and type(row['sha256']) is str
                    and re.fullmatch('[0-9a-f]{64}', row['sha256']) is not None
                    and type(row['size_bytes']) is int and row['size_bytes'] >= 0,
                    'lcer.external_input_invalid')
            path = Path(row['realpath'])
            require(path.is_absolute() and str(path) == row['realpath'] and '..' not in path.parts
                    and len(path.parts) > 1, 'lcer.external_input_invalid')
            previous = self._records.setdefault(row['realpath'], dict(row))
            require(previous == row, 'lcer.external_input_invalid')
        self.verify()

    @staticmethod
    def _stat_key(value):
        return (value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns, value.st_ctime_ns)

    @contextlib.contextmanager
    def _opened(self, path):
        require(path in self._records, 'lcer.external_input_invalid')
        row = self._records[path]
        directory = descriptor = None
        try:
            # Walk by directory descriptors. A swapped ancestor or final
            # symlink cannot redirect the read to another recorded path.
            parts = Path(path).parts
            flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
            directory = os.open(parts[0], flags | os.O_DIRECTORY)
            for part in parts[1:-1]:
                child = os.open(part, flags | os.O_DIRECTORY, dir_fd=directory)
                os.close(directory)
                directory = child
            descriptor = os.open(parts[-1], flags | os.O_NONBLOCK, dir_fd=directory)
            before = os.fstat(descriptor)
            require(stat.S_ISREG(before.st_mode) and before.st_size == row['size_bytes'],
                    'lcer.external_input_changed')
            try:
                yield descriptor
            finally:
                after = os.fstat(descriptor)
                current = os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
                # Also check the absolute name after reads through pinned
                # parents. An ancestor replacement cannot preserve identity.
                require(str(Path(path).resolve(strict=True)) == path
                        and self._stat_key(before) == self._stat_key(after) == self._stat_key(current)
                        == self._stat_key(os.stat(path, follow_symlinks=False)), 'lcer.external_input_changed')
        except OSError as error:
            raise ValueError('lcer.external_input_invalid') from error
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if directory is not None:
                os.close(directory)

    def _consume(self, descriptor, path, retain):
        row = self._records[path]
        hasher = hashlib.sha256()
        chunks = []
        count = 0
        while True:
            raw = os.read(descriptor, min(1048576, row['size_bytes'] - count + 1))
            if not raw:
                break
            count += len(raw)
            require(count <= row['size_bytes'], 'lcer.external_input_changed')
            hasher.update(raw)
            if retain:
                chunks.append(raw)
        require(count == row['size_bytes'] and hasher.hexdigest() == row['sha256'], 'lcer.external_input_changed')
        return b''.join(chunks) if retain else None

    def _read(self, path, retain):
        with self._opened(path) as descriptor:
            return self._consume(descriptor, path, retain)

    @contextlib.contextmanager
    def reader(self, path):
        """Bounded pread access bracketed by complete file hashes and stat checks."""
        with self._opened(path) as descriptor:
            self._consume(descriptor, path, False)
            active = True

            def read_at(offset, count):
                size = self._records[path]['size_bytes']
                require(active and type(offset) is int and type(count) is int and 0 <= offset <= size
                        and 0 <= count <= size - offset, 'lcer.external_input_invalid')
                raw = os.pread(descriptor, count, offset)
                require(len(raw) == count, 'lcer.external_input_changed')
                return raw

            try:
                yield read_at
            finally:
                active = False
                os.lseek(descriptor, 0, os.SEEK_SET)
                self._consume(descriptor, path, False)

    def read(self, path):
        return self._read(path, True)

    def verify(self):
        for path in sorted(self._records):
            self._read(path, False)


def native_shared_cache_inventory(files, main):
    """Derive modern dyld cache membership from authenticated file descriptors.

    Decode Apple's cache header, mappings, v2 subcache entries, both image
    indexes and embedded Mach-O commands. No harness decoder or child summary
    supplies these identities. This proves cache bytes, not process mapping.
    """
    require(isinstance(files, ExternalFileSnapshot) and type(main) is dict
            and main.get('realpath') in files._records and files._records[main['realpath']] == main,
            'lcer.dyld_cache_invalid')
    pending = [(main['realpath'], None, None)]
    readers, cache_uuids, mappings, ordered_files = {}, [], [], []
    primary, family, base = None, None, None

    def uuid_text(raw):
        require(type(raw) is bytes and len(raw) == 16 and any(raw), 'lcer.dyld_cache_invalid')
        value = raw.hex()
        return '-'.join(value[a:b] for a, b in ((0, 8), (8, 12), (12, 16), (16, 20), (20, 32)))

    def read(path, offset, count):
        size = files._records[path]['size_bytes']
        require(type(offset) is int and type(count) is int and 0 <= offset <= size
                and 0 <= count <= size - offset, 'lcer.dyld_cache_invalid')
        return readers[path](offset, count)

    def name_at(path, offset):
        raw = read(path, offset, min(4096, files._records[path]['size_bytes'] - offset))
        value, separator, _ = raw.partition(b'\0')
        require(separator, 'lcer.dyld_cache_invalid')
        try:
            name = value.decode('utf-8')
        except UnicodeError as error:
            raise ValueError('lcer.dyld_cache_invalid') from error
        parsed = Path(name)
        require(parsed.is_absolute() and str(parsed) == name and '..' not in parsed.parts and name != '/',
                'lcer.dyld_cache_invalid')
        return name

    def disjoint(rows, start):
        ordered = sorted(rows, key=lambda row: row[start])
        require(all(left[start] + left['size'] <= right[start] for left, right in zip(ordered, ordered[1:])),
                'lcer.dyld_cache_invalid')

    with contextlib.ExitStack() as stack:
        for path, expected_uuid, expected_offset in pending:
            require(path in files._records and path not in readers, 'lcer.dyld_cache_invalid')
            readers[path] = stack.enter_context(files.reader(path))
            ordered_files.append(dict(files._records[path]))
            header = read(path, 0, 464)
            architecture = {b'dyld_v1  arm64e': 'arm64e', b'dyld_v1   arm64': 'arm64',
                            b'dyld_v1  x86_64': 'x86_64', b'dyld_v1 x86_64h': 'x86_64'}.get(header[:16].rstrip(b'\0'))
            require(architecture is not None and (family is None or architecture == family), 'lcer.dyld_cache_invalid')
            family = architecture
            current_uuid = uuid_text(header[88:104])
            require(current_uuid not in cache_uuids and (expected_uuid is None or current_uuid == expected_uuid),
                    'lcer.dyld_cache_invalid')
            cache_uuids.append(current_uuid)
            mapping_offset, mapping_count = struct.unpack_from('<II', header, 16)
            require(mapping_offset >= 464 and 1 <= mapping_count <= 64, 'lcer.dyld_cache_invalid')
            local = []
            for index in range(mapping_count):
                address, size, offset, maximum, initial = struct.unpack('<QQQII', read(path, mapping_offset + 32 * index, 32))
                require(address and size and address + size < 1 << 64 and offset + size <= files._records[path]['size_bytes']
                        and maximum & ~7 == 0 and initial & ~maximum == 0, 'lcer.dyld_cache_invalid')
                local.append({'address': address, 'size': size, 'offset': offset,
                              'max_protection': maximum, 'initial_protection': initial, 'file': path})
            minimum = min(row['address'] for row in local)
            if base is None:
                base = minimum
            else:
                require(minimum == base + expected_offset, 'lcer.dyld_cache_invalid')
            disjoint(local, 'offset')
            mappings.extend(local)
            sub_offset, sub_count = struct.unpack_from('<II', header, 392)
            require(sub_count <= 64 and (expected_uuid is None or sub_count == 0), 'lcer.dyld_cache_invalid')
            suffixes = set()
            for index in range(sub_count):
                entry = read(path, sub_offset + 56 * index, 56)
                child_uuid = uuid_text(entry[:16])
                vm_offset, = struct.unpack_from('<Q', entry, 16)
                suffix, separator, padding = entry[24:].partition(b'\0')
                require(separator and not any(padding) and re.fullmatch(rb'\.[0-9]+(?:\.[A-Za-z0-9_]+)*', suffix)
                        and suffix not in suffixes, 'lcer.dyld_cache_invalid')
                suffixes.add(suffix)
                pending.append((path + suffix.decode('ascii'), child_uuid, vm_offset))
            text_offset, text_count = struct.unpack_from('<QQ', header, 136)
            image_offset, image_count = struct.unpack_from('<II', header, 448)
            require(text_count <= 100000 and text_count == image_count and (expected_uuid is not None or text_count),
                    'lcer.dyld_cache_invalid')
            texts, images = {}, {}
            for index in range(text_count):
                text = read(path, text_offset + 32 * index, 32)
                address, size, name_offset = struct.unpack_from('<QII', text, 16)
                name = name_at(path, name_offset)
                require(name not in texts and size, 'lcer.dyld_cache_invalid')
                texts[name] = {'address': address, 'size': size, 'macho_uuid': uuid_text(text[:16])}
                address, _, _, name_offset, padding = struct.unpack('<QQQII', read(path, image_offset + 32 * index, 32))
                name = name_at(path, name_offset)
                require(name not in images and padding == 0, 'lcer.dyld_cache_invalid')
                images[name] = address
            require({name: row['address'] for name, row in texts.items()} == images, 'lcer.dyld_cache_invalid')
            if primary is None:
                primary = texts
            else:
                require(not texts or texts == primary, 'lcer.dyld_cache_invalid')
        disjoint(mappings, 'address')
        identities = []
        for name, row in sorted(primary.items()):
            matches = [mapping for mapping in mappings if mapping['address'] <= row['address'] and
                       row['address'] + row['size'] <= mapping['address'] + mapping['size'] and mapping['initial_protection'] & 4]
            require(len(matches) == 1, 'lcer.dyld_cache_invalid')
            mapping = matches[0]
            offset = mapping['offset'] + row['address'] - mapping['address']
            header = read(mapping['file'], offset, 32)
            command_size, = struct.unpack_from('<I', header, 20)
            require(command_size <= row['size'] - 32, 'lcer.dyld_cache_invalid')
            raw = header + read(mapping['file'], offset + 32, command_size)
            try:
                decoded, = native_file_image_headers(raw)
            except ValueError as error:
                raise ValueError('lcer.dyld_cache_invalid') from error
            require(decoded['macho_uuid'] == row['macho_uuid'] and
                    (decoded['architecture'] in ('arm64', 'arm64e') if family in ('arm64', 'arm64e')
                     else decoded['architecture'] == 'x86_64'), 'lcer.dyld_cache_invalid')
            identities.append({'realpath': name, 'sha256': main['sha256'], 'macho_uuid': row['macho_uuid'],
                               'architecture': decoded['architecture'], 'source': 'dyld_shared_cache'})
    return {'main': dict(main), 'files': ordered_files, 'cache_uuids': cache_uuids,
            'images': identities, 'mappings': mappings}


def _build_cache_relations(policy, build_raw, files, image_result):
    """Join every cached loaded image to raw cache identity and file coverage."""
    build = wire(policy, 'build_record', build_raw)
    external = build['external_inputs']
    inventory = native_shared_cache_inventory(files, external['dyld_cache'])
    declared = {row['realpath']: row for row in external['build_inputs']}
    require(len(declared) == len(external['build_inputs']) and
            all(declared.get(row['realpath']) == row for row in inventory['files']), 'lcer.dyld_cache_invalid')
    cached = {row['realpath']: row for row in inventory['images']}
    ordinary = {row['realpath']: {key: value for key, value in row.items() if key != 'file_type'}
                for row in image_result['verified_file_images']}
    rows = external['loaded_images']
    require(len({row['realpath'] for row in rows}) == len(rows), 'lcer.image_identity_invalid')
    expected_cache = []
    for row in rows:
        expected = cached.get(row['realpath']) if row['realpath'] in cached else ordinary.get(row['realpath'])
        require(expected == row and row['architecture'] in ('arm64', 'arm64e'), 'lcer.image_identity_invalid')
        if row['realpath'] in cached:
            expected_cache.append(row)
    require(expected_cache and expected_cache == image_result['unverified_cache_images'], 'lcer.image_identity_invalid')
    return {'cache_files': inventory['files'], 'cache_uuids': inventory['cache_uuids'],
            'verified_cache_images': expected_cache, 'available_cache_images': len(cached)}


def native_build_action_inventory(files, project, engine_root, editor, target_name, log_raw):
    """Recalculate UBT input closure and output identities from pinned disk bytes.

    This checks consistency of captured build metadata, not execution of the
    current source. Source effects, acquisition ownership and compiled class
    coverage remain separate mandatory gates.
    """
    require(isinstance(files, ExternalFileSnapshot), 'lcer.external_input_invalid')
    require(type(target_name) is str and re.fullmatch(r'[A-Za-z0-9_]+Editor', target_name),
            'lcer.build_target_invalid')
    project_root = Path(project).parent
    engine_root = Path(engine_root)
    require(project_root.is_absolute() and engine_root.is_absolute()
            and engine_root.resolve(strict=True) == engine_root, 'lcer.build_target_invalid')
    aliases, used = {}, set()

    def pin(path):
        supplied = Path(path)
        require(supplied.is_absolute() and '\0' not in str(supplied), 'lcer.build_input_path_invalid')
        try:
            actual = supplied.resolve(strict=True)
        except OSError as error:
            raise ValueError('lcer.build_input_path_invalid') from error
        if supplied.is_relative_to(project_root) or actual.is_relative_to(project_root):
            require(not any(parent.is_symlink() for parent in (supplied, *supplied.parents)),
                    'lcer.dependency_path_invalid')
        name = str(actual)
        require(aliases.setdefault(str(supplied), name) == name, 'lcer.external_input_changed')
        require(name in files._records, 'lcer.build_input_missing')
        used.add(name)
        return dict(files._records[name])

    def read(path):
        return files.read(pin(path)['realpath'])

    def product_path(value):
        require(type(value) is str and value and '\0' not in value, 'lcer.build_receipt_invalid')
        for token, root in (('$(EngineDir)', engine_root), ('$(ProjectDir)', project_root)):
            if value[:len(token)].lower() == token.lower():
                tail = value[len(token):]
                require(tail.startswith('/') and '..' not in Path(tail).parts and '$(' not in tail,
                        'lcer.build_receipt_invalid')
                return str(root / tail[1:])
        require(Path(value).is_absolute() and '..' not in Path(value).parts and '$(' not in value,
                'lcer.build_receipt_invalid')
        return value

    project_identity, editor_identity = pin(project), pin(editor)
    archive_path = project_root / 'Intermediate/Build/Mac/arm64' / target_name / 'Development/Makefile.bin'
    receipt_path = project_root / 'Binaries/Mac' / (target_name + '.target')
    archive = NativeUbtArchive(read(archive_path)).decode()
    require(archive['receipt'] == str(receipt_path) and archive['target_type'] == 1 and not archive['test_target']
            and archive['intermediate'] == str(archive_path.parent)
            and archive['intermediate_no_arch'] == str(project_root / 'Intermediate/Build/Mac' / target_name / 'Development'),
            'lcer.build_target_invalid')
    executable = pin(archive['executable'])
    closure = native_ubt_action_closure(archive, log_raw)
    compilers, sdks, linked = {}, {}, set()
    for index in closure['action_indices']:
        action = archive['actions'][index]
        command = pin(action['command'])
        for path in action['prerequisites']:
            pin(path)
        if action['dependency_list'] is not None:
            targets, dependencies = native_clang_dependencies(read(action['dependency_list']))
            targets = {str(Path(os.path.normpath(str(Path(action['cwd']) / path)))) for path in targets}
            require(targets <= set(action['produced']), 'lcer.build_dependencies_invalid')
            for path in dependencies:
                pin(Path(action['cwd']) / path)
        if action['type'] == 7:
            match = re.fullmatch(r'"([^"\\\x00\r\n]+)" -Session="\{[0-9a-fA-F-]{36}\}" '
                                 r'-Mode=WriteMetadata -Input="([^"\\\x00\r\n]+)" -Version=2', action['arguments'])
            require(match is not None and Path(action['command']).name == 'dotnet'
                    and match[1] == str(engine_root / 'Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll')
                    and match[2] in action['prerequisites'], 'lcer.build_metadata_action_invalid')
            pin(match[1])
            pin(match[2])
            continue
        require(action['type'] in (3, 6), 'lcer.build_action_unclassified')
        require(Path(action['command']).name in ('clang', 'clang++'), 'lcer.build_toolchain_invalid')
        compilers[command['realpath']] = command
        match = re.fullmatch(r'@"([^"\\\x00\r\n]+)"', action['arguments'])
        require(match is not None and match[1] in action['prerequisites'] and Path(match[1]).is_absolute(),
                'lcer.build_response_invalid')
        argv = native_ubt_arguments(read(match[1]))
        for value in argv:
            if value.startswith('@'):
                require(not (Path(action['cwd']) / value[1:]).is_file(), 'lcer.build_response_invalid')
        archived = action['response_contents']
        require(type(archived) is list and all(type(line) is str for line in archived)
                and argv == native_ubt_arguments('\n'.join(archived).encode('utf-8')), 'lcer.build_response_changed')
        require(argv.count('-arch') == 1 and argv.count('-isysroot') == 1
                and not any(value.startswith('--sysroot') or (value.startswith('-isysroot') and value != '-isysroot')
                            for value in argv), 'lcer.build_toolchain_invalid')
        arch_at, sdk_at = argv.index('-arch'), argv.index('-isysroot')
        require(arch_at + 1 < len(argv) and argv[arch_at + 1] == 'arm64' and sdk_at + 1 < len(argv)
                and Path(argv[sdk_at + 1]).is_absolute(), 'lcer.build_toolchain_invalid')
        sdk = pin(Path(argv[sdk_at + 1]) / 'SDKSettings.json')
        sdks[sdk['realpath']] = sdk
        if action['type'] == 6:
            for path in action['produced']:
                if path.endswith('.dylib'):
                    linked.add(pin(path)['realpath'])
    require(len(compilers) == len(sdks) == 1, 'lcer.build_toolchain_invalid')
    receipt = strict_json(read(receipt_path), canonical=False)
    expected = {'TargetName': target_name, 'Platform': 'Mac', 'Configuration': 'Development',
                'TargetType': 'Editor', 'Architecture': 'arm64', 'IsTestTarget': False}
    require(all(type(receipt.get(key)) is type(value) and receipt[key] == value for key, value in expected.items())
            and type(receipt.get('Project')) is str, 'lcer.build_receipt_invalid')
    require(pin(receipt_path.parent / receipt['Project']) == project_identity
            and pin(product_path(receipt.get('Launch'))) == editor_identity, 'lcer.build_receipt_invalid')
    products, seen, modules = receipt.get('BuildProducts'), set(), []
    require(type(products) is list and products, 'lcer.build_receipt_invalid')
    for product in products:
        require(type(product) is dict and product.get('Type') in
                ('Executable', 'DynamicLibrary', 'StaticLibrary', 'ImportLibrary', 'SymbolFile',
                 'RequiredResource', 'BuildResource', 'MapFile'), 'lcer.build_receipt_invalid')
        path = product_path(product.get('Path'))
        require(path not in seen, 'lcer.build_receipt_invalid')
        seen.add(path)
        if Path(path).is_relative_to(project_root) and product['Type'] == 'DynamicLibrary':
            identity = pin(path)
            require(identity['realpath'] in linked, 'lcer.build_module_producer_missing')
            raw = files.read(identity['realpath'])
            slices = [row for row in native_file_image_headers(raw) if row['architecture'] in ('arm64', 'arm64e')]
            require(len(slices) == 1 and slices[0]['architecture'] == 'arm64' and slices[0]['file_type'] == 6,
                    'lcer.image_identity_invalid')
            modules.append({'realpath': identity['realpath'], 'sha256': identity['sha256'],
                            'architecture': 'arm64', 'macho_uuid': slices[0]['macho_uuid'], 'source': 'dyld'})
    final = {path for path in linked if Path(path).is_relative_to(project_root)
             and 'Binaries' in Path(path).relative_to(project_root).parts}
    require(modules and final == {row['realpath'] for row in modules} and archive['executable'] in seen,
            'lcer.build_module_producer_missing')
    engine_version = pin(engine_root / 'Build/Build.version')
    files.verify()
    require(all(str(Path(alias).resolve(strict=True)) == value for alias, value in aliases.items()),
            'lcer.external_input_changed')
    return {'archive': pin(archive_path), 'receipt': pin(receipt_path), 'engine_root': str(engine_root),
            'engine_build_version': engine_version, 'compiler': next(iter(compilers.values())),
            'sdk': next(iter(sdks.values())), 'project': project_identity, 'editor': editor_identity,
            'target_executable': executable, 'modules': sorted(modules, key=lambda row: row['realpath']),
            'action_indices': closure['action_indices'], 'executed_action_count': closure['executed_action_count'],
            'required_files': [dict(files._records[path]) for path in sorted(used)]}


def _build_python_relations(policy, build_raw, log_raw, files):
    """Bind the parent's runtime prelude to the recorded interpreter bytes.

    Read the original log and executable independently of the harness. Never
    execute a path supplied by the release. Version strings remain observed
    metadata: these relations do not prove which process emitted the log,
    native callback effects, or successful compiler execution.
    """
    build = wire(policy, 'build_record', build_raw)
    check_index([build['log']], ['build.log'], {'build.log': log_raw})
    require(type(log_raw) is bytes and isinstance(files, ExternalFileSnapshot),
            'lcer.python_runtime_log_invalid')
    prefix = b'CITY_LCER_PYTHON '
    line, newline, compiler = log_raw.partition(b'\n')
    require(newline and line.startswith(prefix) and
            not any(row.startswith(prefix) for row in compiler.splitlines()),
            'lcer.python_runtime_log_invalid')
    runtime = strict_json(line[len(prefix):] + b'\n')
    require(type(runtime) is dict and set(runtime) ==
            {'schema', 'executable', 'implementation', 'version', 'version_info'} and
            runtime['schema'] == 'city.live_evidence_python_runtime.v1',
            'lcer.python_runtime_log_invalid')
    require(all(type(runtime[key]) is str and runtime[key] for key in ('implementation', 'version')) and
            type(runtime['version_info']) is list and len(runtime['version_info']) == 5 and
            all(type(runtime['version_info'][index]) is int and runtime['version_info'][index] >= 0
                for index in (0, 1, 2, 4)) and
            runtime['version_info'][3] in ('alpha', 'beta', 'candidate', 'final'),
            'lcer.python_runtime_log_invalid')
    executable = wire(policy, 'file_identity', stored(runtime['executable']))
    require(executable == build['external_inputs']['python'] and
            files._records.get(executable['realpath']) == executable,
            'lcer.python_runtime_identity_mismatch')
    raw = files.read(executable['realpath'])
    images = native_file_image_headers(raw)
    require(images and all(image['file_type'] == 2 for image in images),
            'lcer.python_runtime_identity_mismatch')
    files.verify()
    return {'runtime': runtime, 'compiler_log': compiler,
            'executable_images': images, 'executable_sha256': digest(raw)}


def _build_action_relations(policy, build_raw, log_raw, files):
    build = wire(policy, 'build_record', build_raw)
    check_index([build['log']], ['build.log'], {'build.log': log_raw})
    external = build['external_inputs']
    observed = native_build_action_inventory(files, build['project']['realpath'], external['engine_root'],
                                            build['editor']['realpath'], 'CityMaterializationProofEditor', log_raw)
    require(all(observed[key] == build[key] for key in ('project', 'editor', 'modules'))
            and all(observed[key] == external[key] for key in ('engine_root', 'engine_build_version', 'compiler', 'sdk')),
            'lcer.build_input_mismatch')
    declared = {row['realpath']: row for row in external['build_inputs']}
    require(all(declared.get(row['realpath']) == row for row in observed['required_files']), 'lcer.build_input_missing')
    return observed


def native_class_inventory(files, image_records, build_inputs, layout_path):
    """Derive class authority from complete bound input and image inventories.

    Images without any constructor-name bytes cannot define a requested UHT
    constructor. Others require the native symbol, instruction and pointer
    decoder. This byte absence check grants no class authority and does not
    suppress malformed registration metadata in a potentially relevant image.
    """
    require(isinstance(files, ExternalFileSnapshot) and type(build_inputs) is list and build_inputs,
            'lcer.native_ancestry_invalid')
    inputs = {row['realpath']: row for row in build_inputs}
    require(len(inputs) == len(build_inputs) and all(files._records.get(path) == row for path, row in inputs.items()),
            'lcer.native_ancestry_invalid')
    generated = sorted(path for path in inputs if path.endswith('.generated.h'))
    require(generated and layout_path in inputs, 'lcer.native_ancestry_invalid')
    sources = {path: files.read(path) for path in generated + [layout_path]}
    require(type(image_records) is list and image_records, 'lcer.image_identity_invalid')
    paths = [row['realpath'] for row in image_records]
    require(paths == sorted(set(paths)) and all(row['source'] == 'dyld' for row in image_records),
            'lcer.image_identity_invalid')
    records = []
    for row in image_records:
        if row['realpath'] in files._records:
            record = dict(files._records[row['realpath']])
            require(record['sha256'] == row['sha256'], 'lcer.image_identity_invalid')
        else:
            try:
                size = os.stat(row['realpath'], follow_symlinks=False).st_size
            except OSError as error:
                raise ValueError('lcer.image_identity_invalid') from error
            record = {'realpath': row['realpath'], 'sha256': row['sha256'], 'size_bytes': size}
        records.append(record)
    image_files = ExternalFileSnapshot(records)
    images = []
    for row in image_records:
        raw = image_files.read(row['realpath'])
        identity = native_file_image_identity(raw, row)
        if b'Z_Construct_UClass_' not in raw:
            continue
        require(identity['file_type'] == 6 and identity['architecture'] == 'arm64', 'lcer.native_ancestry_invalid')
        images.append(NativeMachOImage(raw, row))
    registry = NativeClassRegistry(images, build_inputs, sources, layout_path)
    files.verify()
    image_files.verify()
    return registry


def _build_native_class_relations(policy, build_raw, files):
    build = wire(policy, 'build_record', build_raw)
    external = build['external_inputs']
    images = [row for row in external['loaded_images'] if row['source'] == 'dyld']
    layout = str(Path(external['engine_root']) / 'Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h')
    registry = native_class_inventory(files, images, external['build_inputs'], layout)
    registry.require_classes([policy['runtime']['game_mode'], '/Script/CityLiveEvidenceProof.CityLiveEvidenceActor',
                              '/Script/Engine.Actor', '/Script/Engine.Pawn', '/Script/Engine.Controller'])
    return registry


def _build_file_relations(policy, build_raw):
    """Read every declared file-identity slot in the build record.

    Image UUIDs, shared-cache image membership and UBT action closure require
    separate raw decoders. Matching this declared subset is no build seal.
    """
    build = wire(policy, 'build_record', build_raw)
    external = build['external_inputs']
    records = [build['editor'], build['project']]
    records.extend(external[key] for key in ('engine_build_version', 'compiler', 'sdk', 'python', 'dyld_cache'))
    for key in ('build_inputs', 'engine_configs', 'engine_plugins'):
        rows = external[key]
        paths = [row['realpath'] for row in rows]
        require(paths and paths == sorted(set(paths)), 'lcer.external_input_invalid')
        records.extend(rows)
    return ExternalFileSnapshot(records)


def _build_file_image_relations(policy, build_raw, files):
    """Authenticate ordinary image bytes in the declared loaded-image census.

    Cached-image rows are returned explicitly unverified. The enclosing
    verifier still owes independent cache membership and complete build/class
    authentication before it can open its public acceptance route.
    """
    require(isinstance(files, ExternalFileSnapshot), 'lcer.external_input_invalid')
    build = wire(policy, 'build_record', build_raw)
    images = build['external_inputs']['loaded_images']
    modules = build['modules']
    for rows in (images, modules):
        paths = [row['realpath'] for row in rows]
        require(paths and paths == sorted(set(paths)), 'lcer.image_identity_invalid')
    require(all(row in images and row['source'] == 'dyld' and row['architecture'] == 'arm64' for row in modules),
            'lcer.image_identity_invalid')
    declared_files = [row for row in images if row['source'] == 'dyld']
    cached = [row for row in images if row['source'] == 'dyld_shared_cache']
    records = []
    for row in declared_files:
        require(type(row['realpath']) is str and '\0' not in row['realpath'], 'lcer.image_identity_invalid')
        if row['realpath'] in files._records:
            record = dict(files._records[row['realpath']])
            require(record['sha256'] == row['sha256'], 'lcer.image_identity_invalid')
        else:
            try:
                size = os.stat(row['realpath'], follow_symlinks=False).st_size
            except OSError as error:
                raise ValueError('lcer.image_identity_invalid') from error
            record = {'realpath': row['realpath'], 'sha256': row['sha256'], 'size_bytes': size}
        records.append(record)
    snapshot = ExternalFileSnapshot(records)
    checked = {row['realpath']: native_file_image_identity(snapshot.read(row['realpath']), row) for row in declared_files}
    editor = build['editor']
    require(editor['realpath'] in checked and checked[editor['realpath']]['file_type'] == 2
            and checked[editor['realpath']]['architecture'] == 'arm64'
            and checked[editor['realpath']]['sha256'] == editor['sha256']
            and all(checked[row['realpath']]['file_type'] == 6 for row in modules), 'lcer.image_identity_invalid')
    files.verify()
    snapshot.verify()
    return {'verified_file_images': [checked[path] for path in sorted(checked)], 'unverified_cache_images': cached}


def _current_git_identity(repository):
    """Read and hash actual HEAD commit/tree objects with Git indirection closed.

    These are provenance reads. They neither require a clean candidate tree nor
    claim that uncommitted release source belongs to the recorded commit tree.
    The postcommit closure gate separately requires its exact committed source.
    """
    repository = Path(repository)
    require(repository.is_absolute() and repository == repository.resolve() and
            not any(path.is_symlink() for path in (repository, *repository.parents)), 'lcer.source_git_identity_invalid')
    environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
                   'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_OPTIONAL_LOCKS': '0', 'GIT_NO_REPLACE_OBJECTS': '1'}

    def command(arguments):
        try:
            result = subprocess.run(['/usr/bin/git', *arguments], cwd=repository, env=environment,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ValueError('lcer.source_git_identity_invalid') from error
        require(result.returncode == 0 and len(result.stdout) <= 1048576, 'lcer.source_git_identity_invalid')
        return result.stdout

    raw = command(['rev-parse', '--show-toplevel', 'HEAD', 'HEAD^{tree}'])
    try:
        lines = raw.decode('utf-8').splitlines()
    except UnicodeError as error:
        raise ValueError('lcer.source_git_identity_invalid') from error
    require(len(lines) == 3 and lines[0] == str(repository) and all(re.fullmatch('[0-9a-f]{40}', value)
            for value in lines[1:]), 'lcer.source_git_identity_invalid')
    commit = command(['cat-file', 'commit', lines[1]])
    object_hash = hashlib.sha1(b'commit ' + str(len(commit)).encode('ascii') + b'\0' + commit).hexdigest()
    require(object_hash == lines[1] and commit.startswith(('tree ' + lines[2] + '\n').encode('ascii')),
            'lcer.source_git_identity_invalid')
    tree = command(['cat-file', 'tree', lines[2]])
    tree_hash = hashlib.sha1(b'tree ' + str(len(tree)).encode('ascii') + b'\0' + tree).hexdigest()
    require(tree_hash == lines[2], 'lcer.source_git_identity_invalid')
    require(command(['rev-parse', 'HEAD', 'HEAD^{tree}']) == (lines[1] + '\n' + lines[2] + '\n').encode('ascii'),
            'lcer.source_git_identity_invalid')
    return {'source_commit': lines[1], 'source_tree': lines[2]}


def _source_identity_relations(context):
    """Bind release bytes and recorded Git identity to current canonical CITY.

    Negative release copies may live elsewhere. Their launch/build authority
    still names CITY. Recheck all seventy source members there, with Git reads
    before and after. This is development freshness, not a trusted snapshot or
    a claim that a dirty candidate has been committed.
    """
    policy, artifacts, sources = context['policy'], context['artifacts'], context['source_bytes']
    repository = Path('/Users/boandersson/Projects/CITY')
    prefix = policy['runtime']['output_root'] + '/'
    members = {name for name in policy['release_members'] if not name.startswith(prefix)}
    require(type(sources) is dict and set(sources) == members and len(members) == 70,
            'lcer.source_identity_mismatch')
    before = _current_git_identity(repository)
    build = wire(policy, 'build_record', artifacts['build.json'])
    acquisition = wire(policy, 'acquisition_record', artifacts['acquisition.json'])
    require(all(build[key] == acquisition[key] == value for key, value in before.items()), 'lcer.source_identity_mismatch')
    for name, raw in sources.items():
        require(type(raw) is bytes and ordinary_file(repository, name) == raw, 'lcer.source_identity_mismatch')
    require(_current_git_identity(repository) == before, 'lcer.source_identity_mismatch')
    return before


def _binding_relations(policy, supplied, startup_raw, observation, project,
                       process_root, operator_user, class_parents):
    """Independently derive the binding and check its initial world.

    The enclosing verifier must authenticate the original trace, build and
    external inventories, class graph and retained pipe ownership separately.
    A self-consistent supplied record is never proof of those observations.
    No candidate Python or binding constructor is called here.
    """
    binding = wire(policy, 'process_binding', stored(supplied))
    startup = wire(policy, 'startup', startup_raw)
    process = wire(policy, 'process_observation', stored(observation))
    project = wire(policy, 'file_identity', stored(project))
    base = '/Users/boandersson/Projects/CITY'
    require(type(process_root) is str and type(operator_user) is str and bool(operator_user))
    root = Path(process_root)
    require(root.is_absolute() and str(root) == process_root and '..' not in root.parts)
    require(same_json(startup, process['startup']) and process['pid'] > 0 and process['ppid'] > 0)
    require(startup['pid'] == process['pid'] and startup['cwd_realpath'] == process['cwd_realpath'] == base)
    require(project['realpath'] == base + '/' + policy['runtime']['project'] and
            project['sha256'] == policy['unchanged_dependencies'][policy['runtime']['project']])
    substitutions = dict(engine=policy['runtime']['engine'], absolute_city_project=project['realpath'],
                         absolute_domain_root=process_root, observed_operator_user=operator_user,
                         witness_id=startup['witness_id'], domain=startup['domain'], launch_id=startup['launch_id'])
    require(process['argv'] == [value.format_map(substitutions) for value in policy['launch_argv']])
    require(process['environment'] == {name: value.format_map(substitutions)
                                       for name, value in policy['launch_environment'].items()})
    require(process['executable']['realpath'] == policy['runtime']['engine'])
    require(same_json(process['loaded_images'], startup['loaded_images']))
    for field in ('loaded_images', 'enabled_plugins', 'config_files'):
        names = [row['realpath'] for row in startup[field]]
        require(bool(names) and names == sorted(set(names)))
        require(all(Path(name).is_absolute() and str(Path(name)) == name and '..' not in Path(name).parts
                    for name in names))
    require(startup['proof_module']['source'] == 'dyld' and
            any(same_json(startup['proof_module'], row) for row in startup['loaded_images']))
    file_numbers = [row['fd'] for row in process['descriptors']]
    require(file_numbers == sorted(set(file_numbers)) and
            all(row['pid'] == process['pid'] for row in process['descriptors']))
    pipes = []
    for number, access in enumerate(('read', 'write', 'write')):
        matches = [row for row in process['descriptors'] if row['fd'] == number]
        require(len(matches) == 1)
        row = matches[0]
        require(row['kind'] == 'pipe' and row['access'] == access and row['path'] is None and
                row['peer_kernel_id'] is not None)
        pipes.append(row)
    require(len({identity for row in pipes for identity in (row['kernel_id'], row['peer_kernel_id'])}) == 6)
    expected = {'witness_id': startup['witness_id'], 'domain': startup['domain'], 'launch_id': startup['launch_id'],
                'pid': process['pid'], 'macos_birth_tuple': process['macos_birth_tuple'],
                'executable_realpath': process['executable']['realpath'],
                'executable_sha256': process['executable']['sha256'],
                'project_realpath': project['realpath'], 'project_sha256': project['sha256'],
                'module_inventory_sha256': digest(stored(process['loaded_images'])),
                'argv_sha256': digest(stored(process['argv'])),
                'environment_sha256': digest(stored(process['environment'])),
                'descriptor_map_sha256': digest(stored(pipes)), 'process_root_realpath': process_root,
                'cwd_sha256': digest(stored(process['cwd_realpath'])), 'startup_sha256': digest(startup_raw),
                'input_inventory_sha256': digest(stored({field: startup[field] for field in
                    ('loaded_images', 'enabled_plugins', 'config_files', 'proof_module')}))}
    require(same_json(binding, expected), 'lcer.binding_mismatch')
    return _startup_world(policy, startup, class_parents)


def main():
    parser = argparse.ArgumentParser(description="Verify the frozen live evidence release")
    routes = parser.add_subparsers(dest="route", required=True)
    verify = routes.add_parser("verify"); verify.add_argument("--artifacts", required=True)
    args = parser.parse_args()
    try:
        context, canonical = authenticated_imports(RELEASE_ROOT, args.artifacts)
        # Run the independently derived raw trace, process, canonical, world,
        # native input and acquisition predicates on the normal public route.
        # Their internal return value is not release acceptance: complete
        # source-effect auditing and executed-build/fresh-root proof remain
        # outstanding. Keep that final boundary closed after these checks.
        _release_protocol_relations(context, canonical)
        raise ValueError("lcer.release_semantics_not_implemented")
    except (ValueError, OSError, KeyError, TypeError, SyntaxError) as error:
        code = str(error) if isinstance(error, ValueError) else "lcer.release_evidence_invalid"
        print(json.dumps({"status": "fail", "failure_codes": [code]}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
