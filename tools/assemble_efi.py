"""Assemble EFI offline by exact hashes from user-supplied directories or ZIPs.

This tool downloads and executes nothing. The public config is always supplied
by the repository. Matching all files is not a hardware boot qualification.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_FILES = 100000
MAX_MANIFEST_FILES = 4096
MAX_FILE_BYTES = 128 * 1024 * 1024
MAX_MANIFEST_BYTES = 512 * 1024 * 1024
MAX_SOURCE_BYTES = 1024 * 1024 * 1024
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024


class AssemblyError(ValueError):
    def __init__(self, message, missing=None):
        super().__init__(message)
        self.missing = missing


def require(condition, message):
    if not condition:
        raise AssemblyError(message)


def reparse(path):
    record = path.lstat()
    return stat.S_ISLNK(record.st_mode) or bool(getattr(record, 'st_file_attributes', 0) & 0x400)


def clean_existing_parents(path):
    """Reject links before resolve() can hide the original source/output route."""
    path = Path(os.path.abspath(path))
    for item in (path, *path.parents):
        try:
            linked = reparse(item)
        except FileNotFoundError:
            continue
        require(not linked, 'Symbolic links and junctions are not accepted: ' + str(item))
    return path.resolve()


def manifest_name(name):
    require(isinstance(name, str) and bool(name), 'Invalid manifest path')
    parts = name.split('/')
    require(not PurePosixPath(name).is_absolute() and '\\' not in name and
            all(part not in ('', '.', '..') for part in parts), 'Unsafe manifest path: ' + name)
    for part in parts:
        require(not re.search(r'[\x00-\x1f<>:"|?*]', part) and not part.endswith((' ', '.')),
                'Unsafe manifest component: ' + name)
        require(not re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part, re.I),
                'Reserved manifest component: ' + name)
    return name


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def load_manifest(root):
    path = root / 'metadata/assembly-manifest.json'
    clean_existing_parents(path)
    require(path.is_file() and not reparse(path), 'Missing regular metadata/assembly-manifest.json')
    require(path.stat().st_size <= 4 * 1024 * 1024, 'Assembly manifest is too large')
    data = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)
    require(isinstance(data, dict) and data.get('schema') == 1 and data.get('profile') == 'current',
            'Unsupported assembly manifest')
    files = data.get('files')
    require(isinstance(files, dict) and 0 < len(files) <= MAX_MANIFEST_FILES, 'Invalid manifest file count')
    folded = set()
    total = 0
    for name, record in files.items():
        manifest_name(name)
        require(name.casefold() not in folded, 'Case-colliding manifest path: ' + name)
        folded.add(name.casefold())
        require(isinstance(record, dict) and type(record.get('bytes')) is int and
                0 <= record['bytes'] <= MAX_FILE_BYTES and isinstance(record.get('sha256'), str) and
                re.fullmatch(r'[0-9a-f]{64}', record['sha256']) is not None,
                'Invalid manifest record: ' + name)
        total += record['bytes']
    require(total <= MAX_MANIFEST_BYTES, 'Manifest payload exceeds size limit')
    for name in folded:
        parts = name.split('/')
        require(not any('/'.join(parts[:n]) in folded for n in range(1, len(parts))),
                'Manifest file/directory collision: ' + name)
    require('OC/config.plist' in files, 'Manifest does not include the public config')
    return files


def read_file(path, expected):
    with path.open('rb') as stream:
        record = os.fstat(stream.fileno())
        require(stat.S_ISREG(record.st_mode) and record.st_size == expected,
                'Source changed while opening')
        payload = stream.read(expected + 1)
    require(len(payload) == expected, 'Source changed while reading')
    return payload


def safe_zip_name(name):
    require(isinstance(name, str) and name and not name.startswith(('/', '\\')) and
            '\\' not in name and ':' not in name and '\x00' not in name and
            '..' not in name.split('/'), 'Unsafe ZIP member path')


def assemble(root, sources, output):
    root = clean_existing_parents(Path(root))
    require(root.is_dir(), 'Repository root does not exist')
    output = clean_existing_parents(Path(output))
    require(not output.is_relative_to(root), 'Output must be outside the repository')
    require(not output.exists(), 'Output already exists')
    files = load_manifest(root)
    inputs = [clean_existing_parents(Path(source)) for source in sources]
    for source in inputs:
        require(source.exists() and (source.is_file() or source.is_dir()), 'Source is not a regular file or directory: ' + str(source))
        require(not source.is_relative_to(output) and not output.is_relative_to(source),
                'Source and output overlap')
        require(not (source.is_file() and not zipfile.is_zipfile(source)), 'Source file must be a ZIP archive: ' + str(source))

    wanted = {}
    sizes = set()
    for name, record in files.items():
        wanted.setdefault((record['bytes'], record['sha256']), []).append(name)
        sizes.add(record['bytes'])
    found = {}
    count = 0
    total = 0

    def account(size):
        nonlocal count, total
        count += 1
        total += size
        require(count <= MAX_FILES and total <= MAX_SOURCE_BYTES and size <= MAX_FILE_BYTES,
                'Source file count or size limit exceeded')

    def match(payload):
        key = (len(payload), hashlib.sha256(payload).hexdigest())
        for name in wanted.get(key, ()):
            found.setdefault(name, payload)

    def directory(source):
        for current, directories, names in os.walk(source, followlinks=False):
            parent = Path(current)
            require(not reparse(parent), 'Source directory contains a link or junction')
            account(0)
            for name in directories:
                require(not reparse(parent / name), 'Source directory contains a link or junction')
            for name in names:
                path = parent / name
                record = path.lstat()
                require(stat.S_ISREG(record.st_mode) and not reparse(path), 'Source contains a nonregular file')
                account(record.st_size)
                if record.st_size in sizes:
                    payload = read_file(path, record.st_size)
                    match(payload)

    public = root / 'EFI'
    require(public.is_dir() and not reparse(public), 'Repository EFI directory is missing')
    directory(public)
    public_config = public / 'OC/config.plist'
    require(public_config.is_file() and not reparse(public_config), 'Public config is missing')
    record = files['OC/config.plist']
    config = read_file(public_config, record['bytes'])
    require(len(config) == record['bytes'] and hashlib.sha256(config).hexdigest() == record['sha256'],
            'Repository public config differs from the assembly manifest')
    # The configured public template remains authoritative, even when a full
    # private EFI is one of the sources.
    found['OC/config.plist'] = config

    for source in inputs:
        if source.is_dir():
            directory(source)
        else:
            require(source.stat().st_size <= MAX_ARCHIVE_BYTES, 'Source ZIP exceeds size limit')
            with zipfile.ZipFile(source) as archive:
                entries = archive.infolist()
                require(len(entries) <= MAX_FILES and sum(item.file_size for item in entries) <= MAX_ARCHIVE_BYTES,
                        'ZIP uncompressed count or size limit exceeded')
                for entry in entries:
                    safe_zip_name(entry.filename)
                    kind = (entry.external_attr >> 16) & 0o170000
                    require(kind not in (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO, stat.S_IFSOCK),
                            'ZIP contains a link or special file')
                    require(not entry.flag_bits & 1, 'Encrypted ZIP sources are not supported')
                    if entry.is_dir():
                        account(0)
                        continue
                    account(entry.file_size)
                    if entry.file_size in sizes:
                        with archive.open(entry) as stream:
                            payload = stream.read(entry.file_size + 1)
                        require(len(payload) == entry.file_size, 'ZIP member size differs')
                        match(payload)

    missing = sorted(set(files) - set(found))
    if missing:
        raise AssemblyError('Required files are missing or do not match the pinned hashes', missing)
    # No output or staging directory is created until every required byte is
    # available. ZIP member names never determine destination paths.
    clean_existing_parents(output)
    require(not output.exists(), 'Output already exists')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.efi-assembly-', dir=output.parent) as temporary:
        staging = Path(temporary) / 'EFI'
        staging.mkdir()
        for name, payload in sorted(found.items()):
            destination = staging.joinpath(*name.split('/'))
            require(destination.resolve().is_relative_to(staging.resolve()), 'Output path escaped staging')
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as stream:
                stream.write(payload)
        require(not output.exists(), 'Output already exists')
        staging.rename(output)
    return {'status': 'assembled-files-only', 'files': len(files), 'output': str(output), 'bootTested': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Repository root (default: this script parent)')
    parser.add_argument('--source', action='append', type=Path, default=[], help='Read-only full EFI directory or official release ZIP; repeat as needed')
    parser.add_argument('--output', type=Path, required=True, help='New destination outside the repository; existing paths are refused')
    args = parser.parse_args()
    try:
        result = assemble(args.root, args.source, args.output)
    except (AssemblyError, OSError, zipfile.BadZipFile, RuntimeError, json.JSONDecodeError) as error:
        result = {'error': str(error)}
        if isinstance(error, AssemblyError) and error.missing is not None:
            result['missing'] = error.missing
        print(json.dumps(result, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
