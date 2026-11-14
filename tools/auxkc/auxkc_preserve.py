#!/usr/bin/env python3
"""Review and build an AuxKC candidate without replacing the live collection.

SPDX-License-Identifier: MIT
Copyright (c) 2026 gndb
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import stat
import subprocess
import sys
import tempfile

SCHEMA = 'auxkc-preservation-plan/1'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def absolute(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'Use an absolute path without parent traversal')
    for entry in [path, *path.parents]:
        if entry.exists() or entry.is_symlink():
            require(not entry.is_symlink() and not stat.S_ISLNK(entry.lstat().st_mode), 'Symlink paths are not supported')
    return path


def tree(path):
    path = absolute(path)
    require(path.is_dir(), 'Bundle directory is absent')
    result = {}
    for entry in sorted(path.rglob('*')):
        require(not entry.is_symlink(), 'Symlink bundle contents are not supported')
        if entry.is_file():
            result[entry.relative_to(path).as_posix()] = {
                'bytes': entry.stat().st_size, 'sha256': file_sha(entry)}
    require(bool(result), 'Empty bundle is not a reviewed input')
    return result


def identity(bundle):
    value = plistlib.loads((Path(bundle) / 'Contents/Info.plist').read_bytes())
    ident, version = value.get('CFBundleIdentifier'), value.get('CFBundleVersion')
    require(isinstance(ident, str) and re.fullmatch(r'[A-Za-z0-9_.-]+', ident), 'Invalid bundle identifier')
    require(isinstance(version, str) and re.fullmatch(r'[A-Za-z0-9.+_-]+', version), 'Invalid bundle version')
    return (ident, version)


def auxiliary_members(text):
    """Parse only the auxiliary section, never Boot/System collection rows."""
    rows, active, found = [], False, False
    for line in text.splitlines():
        if re.match(r'^auxiliary kext collection at ', line):
            require(not found, 'Multiple auxiliary sections are ambiguous')
            active, found = True, True
            continue
        if re.match(r'^(boot|system) kernel collection at ', line):
            active = False
            continue
        if not active or not line.strip() or line == 'Extension Information:':
            continue
        columns = line.split('\t')
        require(len(columns) == 3 or (len(columns) == 4 and not columns[3]), 'Malformed extension information row')
        ident, version, name = columns[:3]
        require(re.fullmatch(r'[A-Za-z0-9_.-]+', ident) and re.fullmatch(r'[A-Za-z0-9.+_-]+', version), 'Malformed extension identity')
        normalized = name.replace('\\', '/')
        require(re.match(r'^(?:/|[A-Za-z]:/).+\.kext$', normalized) and
                not re.search(r'[\x00-\x1f\x7f]', name) and
                '//' not in normalized and
                not any(part in ('.', '..') for part in normalized.split('/')), 'Malformed extension path')
        rows.append((ident, version, name))
    require(found, 'No auxiliary collection section; inspect format may have changed')
    return rows


def local_bundles(root):
    root = absolute(root)
    require(root.is_dir(), 'Extensions directory is absent')
    return sorted(str(p) for p in root.glob('*.kext') if p.is_dir())


def create_plan(inspection, extensions, boot, system, existing, exclude_ids=()):
    extensions, boot, system, existing = map(absolute, (extensions, boot, system, existing))
    excluded = sorted(set(exclude_ids))
    require(len(excluded) == len(exclude_ids), 'Duplicate excluded identifiers')
    require(all(re.fullmatch(r'[A-Za-z0-9_.-]+', x) for x in excluded), 'Invalid excluded identifier')
    local = local_bundles(extensions)
    paths = set(local)
    required = set(identity(p) for p in local)
    for ident, old_version, name in auxiliary_members(inspection):
        if ident in excluded:
            continue
        bundle = absolute(name)
        require(bundle.suffix == '.kext' and bundle.is_dir(), 'Existing AuxKC bundle is unavailable')
        current = identity(bundle)
        require(current[0] == ident, 'Existing bundle identifier changed; review replacement explicitly')
        required.add(current)  # A reviewed installed replacement may have a new version.
        if not any(bundle == Path(p) or Path(p) in bundle.parents for p in local):
            paths.add(str(bundle))
    # A parent bundle includes its plug-ins; do not pass both as duplicate inputs.
    selected = [p for p in sorted(paths) if not any(Path(q) in Path(p).parents for q in paths if q != p)]
    require(selected and required, 'No reviewed bundle inputs')
    manifests = {p: tree(p) for p in selected}
    return {'schema': SCHEMA, 'extensions': str(extensions), 'localBundlePaths': local,
            'bundlePaths': selected, 'bundleManifests': manifests,
            'requiredIdentities': [list(x) for x in sorted(required)],
            'excludedExistingIdentifiers': excluded,
            'bootKC': str(boot), 'systemKC': str(system), 'existingAuxKC': str(existing),
            'kernelCollectionHashes': {str(p): file_sha(p) for p in (boot, system, existing)},
            'note': 'Private local review plan; do not publish it without sanitizing paths.'}


def validate_plan(plan):
    require(plan.get('schema') == SCHEMA, 'Unsupported plan schema')
    paths, manifests = plan['bundlePaths'], plan['bundleManifests']
    require(paths and len(paths) == len(set(paths)) and set(paths) == set(manifests), 'Bundle paths and manifests differ')
    require(local_bundles(plan['extensions']) == plan['localBundlePaths'], 'Local bundle set changed')
    for name in paths:
        require(tree(absolute(name)) == manifests[name], 'Reviewed bundle bytes changed')
    for name, expected in plan['kernelCollectionHashes'].items():
        require(file_sha(absolute(name)) == expected, 'Kernel collection input changed')
    identities = plan['requiredIdentities']
    require(identities and all(isinstance(x, list) and len(x) == 2 and all(isinstance(v, str) for v in x) for x in identities), 'Invalid required identities')


def command(argv):
    return subprocess.run([str(x) for x in argv], capture_output=True, text=True)


def build_candidate(plan, output, logs, runner=command, interrupt=lambda: None):
    output, logs = absolute(output), absolute(logs)
    require(output != Path(plan['existingAuxKC']), 'The live AuxKC is never a candidate destination')
    require(not output.exists(), 'Candidate destination already exists')
    require(output.parent.is_dir() and not logs.exists(), 'Use an existing candidate parent and a new log directory')
    validate_plan(plan)
    logs.mkdir()
    interrupt()
    with tempfile.TemporaryDirectory(prefix='.auxkc-candidate-', dir=str(output.parent)) as temporary:
        candidate = Path(temporary) / 'AuxiliaryKernelExtensions.kc'
        argv = ['/usr/bin/kmutil', 'create', '-n', 'aux', '-x', '-z', '-V', 'release', '-r', plan['extensions']]
        if plan.get('allowMissingKDK', False):
            argv.append('--allow-missing-kdk')
        for name in plan['bundlePaths']:
            argv.extend(['-p', name])
        argv.extend(['-B', plan['bootKC'], '-S', plan['systemKC'], '-A', str(candidate), '--no-authentication'])
        result = runner(argv)
        (logs / 'create.log').write_text(result.stdout + '\n' + result.stderr, encoding='utf-8')
        require(result.returncode == 0 and candidate.is_file(), 'AuxKC candidate generation failed')
        interrupt()
        inspected = runner(['/usr/bin/kmutil', 'inspect', '-A', str(candidate), '-B', plan['bootKC'],
                            '-S', plan['systemKC'], '-V', 'release', '--no-variant-extension', '--show-extension-info'])
        (logs / 'inspect.log').write_text(inspected.stdout + '\n' + inspected.stderr, encoding='utf-8')
        require(inspected.returncode == 0, 'Candidate inspection failed')
        present = {(ident, version) for ident, version, path in auxiliary_members(inspected.stdout)}
        require(set(map(tuple, plan['requiredIdentities'])).issubset(present), 'Candidate omits required bundle identities')
        validate_plan(plan)
        interrupt()
        os.chmod(candidate, 0o644)
        # Temporary and destination are on the same filesystem. Link fails if a
        # destination appeared, rather than replacing a user's existing file.
        os.link(candidate, output)
        candidate.unlink()
    receipt = {'schema': 'auxkc-candidate-result/1', 'candidateSHA256': file_sha(output),
               'requiredIdentitiesVerified': len(plan['requiredIdentities']),
               'bundleCount': len(plan['bundlePaths']), 'liveCollectionReplaced': False,
               'hardwareBootTestPerformed': False}
    (logs / 'result.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    capture = sub.add_parser('plan')
    capture.add_argument('--inspection', type=Path, required=True, help='Previously saved kmutil inspect --show-extension-info output')
    capture.add_argument('--extensions', type=Path, default=Path('/Library/Extensions'))
    capture.add_argument('--boot-kc', type=Path, default=Path('/System/Library/KernelCollections/BootKernelExtensions.kc'))
    capture.add_argument('--system-kc', type=Path, default=Path('/System/Library/KernelCollections/SystemKernelExtensions.kc'))
    capture.add_argument('--existing-aux-kc', type=Path, default=Path('/Library/KernelCollections/AuxiliaryKernelExtensions.kc'))
    capture.add_argument('--exclude-existing-id', action='append', default=[], help='Explicitly removed bundle ID, never an automatic exclusion')
    capture.add_argument('--allow-missing-kdk', action='store_true', help='Use only when the target kmutil supports it')
    capture.add_argument('--output', type=Path, required=True)
    build = sub.add_parser('build-candidate')
    build.add_argument('--plan', type=Path, required=True)
    build.add_argument('--candidate', type=Path, required=True)
    build.add_argument('--logs', type=Path, required=True)
    args = parser.parse_args()
    if args.operation == 'plan':
        require(not args.output.exists(), 'Plan output already exists')
        plan = create_plan(args.inspection.read_text(encoding='utf-8'), args.extensions,
                           args.boot_kc, args.system_kc, args.existing_aux_kc, args.exclude_existing_id)
        plan['allowMissingKDK'] = args.allow_missing_kdk
        args.output.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'planWritten': True, 'bundleCount': len(plan['bundlePaths'])}))
    else:
        require(sys.platform == 'darwin', 'Actual candidate generation is macOS-only')
        result = build_candidate(json.loads(args.plan.read_text(encoding='utf-8')), args.candidate, args.logs)
        print(json.dumps(result))


if __name__ == '__main__':
    main()
