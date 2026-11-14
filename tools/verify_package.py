"""Verify published EFI snapshots and evidence, without claiming a boot test.

No third-party dependency is installed or downloaded. --efi additionally checks
the selected profile's known files in an already assembled, separate EFI tree.
"""
from pathlib import Path, PurePosixPath
import argparse
import copy
import hashlib
import json
import plistlib
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GUID = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
NEW = {'current', 'usable-20261114', 'usb-experimental'}
OLD = {'historical-current', 'dual-tested', 'igpu-only'}
ALL = NEW | OLD
WEX = 'OC/Kexts/WhateverXe.kext/Contents/'
SOURCE_DIRS = ('src/WhateverXe', 'src/WhateverXe-0.8.0-R16-historical')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def relative_path(root, name):
    require(isinstance(name, str) and bool(name), 'Empty manifest path')
    parts = PurePosixPath(name)
    require('\\' not in name and ':' not in name and not parts.is_absolute() and
            all(x not in ('', '.', '..') for x in name.split('/')) and
            not re.match(r'^[A-Za-z]:', name), 'Path outside package: ' + name)
    path = root.joinpath(*parts.parts)
    require(path.resolve().is_relative_to(root.resolve()), 'Path outside package: ' + name)
    require(not path.is_symlink(), 'Symlink is not a published file: ' + name)
    return path


def tree_files(root, exclusions=()):
    result = set()
    for path in root.rglob('*'):
        name = path.relative_to(root).as_posix()
        if name.split('/')[0] == '.git' or name in exclusions:
            continue
        require(not path.is_symlink(), 'Symlink in package: ' + name)
        if path.is_file():
            relative_path(root, name)
            result.add(name)
    return result


def check_files(root, expected, exact=False, exclusions=()):
    require(isinstance(expected, dict), 'Manifest files must be an object')
    for name, record in expected.items():
        path = relative_path(root, name)
        require(isinstance(record, dict) and type(record.get('bytes')) is int and
                record['bytes'] >= 0 and isinstance(record.get('sha256'), str) and
                re.fullmatch(r'[0-9a-f]{64}', record['sha256']) is not None,
                'Invalid manifest record: ' + name)
        require(path.is_file(), 'Missing: ' + name)
        require(path.stat().st_size == record['bytes'] and digest(path) == record['sha256'],
                'Hash mismatch: ' + name)
    if exact:
        actual = tree_files(root, exclusions)
        require(actual == set(expected), 'Manifest tree differs; missing=%s extra=%s' %
                (sorted(set(expected) - actual), sorted(actual - set(expected))))


def check_sanitized_config(config):
    generic = config['PlatformInfo']['Generic']
    for key in ('MLB', 'SystemSerialNumber', 'SystemUUID'):
        require(key in generic and generic[key] == '', 'Identity is not empty: ' + key)
    require(generic.get('ROM') == bytes(6), 'ROM must be six zero bytes')
    security = config['Misc']['Security']
    for key in ('PasswordHash', 'PasswordSalt'):
        require(key in security and security[key] in (b'', ''), 'Password field is not empty: ' + key)
    for values in config['NVRAM']['Add'].values():
        for key, value in values.items():
            if key.lower().startswith('bluetooth') and ('info' in key.lower() or 'address' in key.lower()):
                require(not value, 'Bluetooth identity is not empty: ' + key)
    tokens = config['NVRAM']['Add'][GUID]['boot-args'].split()
    require('-wex-r16-backlight64' in tokens, 'Missing retained backlight64 opt-in')
    forbidden = ('-wex-r16-240hz', '-wex-r16-resume-r10', '-wex-r16-dim-r11')
    require(not any(token.startswith(forbidden) for token in tokens), 'Disabled high-refresh/R10/R11 option is enabled')
    require('nmhybrid=1' not in tokens, 'Unqualified nmhybrid option is enabled')
    require(all(entry['Enabled'] for entry in config['Kernel']['Add']), 'Disabled donor Kernel/Add entry remains')
    return tokens


def check_payload_version(efi, row_id, meta, source):
    version = '0.8.2' if row_id in NEW else '0.8.0'
    info = plistlib.loads(relative_path(efi, WEX + 'Info.plist').read_bytes())
    require(info.get('CFBundleVersion') == version, 'Mixed WEX cohort: ' + row_id)
    actual = digest(relative_path(efi, WEX + 'MacOS/WhateverXe'))
    # Some immutable historical metadata predates the explicit cohort fields;
    # its exact binary is still pinned by the historical source manifest.
    recorded_hash = meta.get('WhateverXeSHA256', source['binarySHA256']) if row_id in OLD else meta['WhateverXeSHA256']
    require(actual == recorded_hash == source['binarySHA256'],
            'WEX binary/source cohort differs: ' + row_id)
    nv_version = '3.0' if row_id in NEW else '2.7.2'
    recorded_nv = meta.get('NVIDIAVersion', nv_version) if row_id in OLD else meta['NVIDIAVersion']
    require(recorded_nv == nv_version, 'Mixed NVIDIA cohort: ' + row_id)
    return actual


def check_profile(root, row, sources):
    row_id = row['id']
    require(row.get('expectedWEX', '0.8.2' if row_id in NEW else '0.8.0') ==
            ('0.8.2' if row_id in NEW else '0.8.0'), 'Profile WEX version label differs: ' + row_id)
    efi = relative_path(root, row['efi'])
    config_path = relative_path(root, row['config'])
    require(config_path == efi / 'OC/config.plist', 'Config is not inside selected EFI: ' + row_id)
    config = plistlib.loads(config_path.read_bytes())
    meta = read_json(relative_path(root, row['metadata']))
    tokens = check_sanitized_config(config)
    require(('-nvoff' in tokens) == (row_id == 'igpu-only'), 'NVIDIA enable state differs: ' + row_id)
    require(meta.get('highRefreshEnabled') is False, 'High refresh must remain disabled: ' + row_id)
    require(meta.get('experimentalUSB', False) is (row_id == 'usb-experimental'), 'USB experiment scope differs: ' + row_id)
    require(digest(config_path) == meta['publicConfigSHA256'], 'Public config hash differs: ' + row_id)
    manifest = read_json(relative_path(root, row['manifest']))
    check_files(efi, manifest, exact=True)
    require(not list((efi / 'OC').glob('config.*.plist')), 'Backup config in EFI: ' + row_id)
    require(not list((efi / 'OC/Kexts').glob('WhateverXe.before-*')), 'Backup WEX in EFI: ' + row_id)
    source = sources[0 if row_id in NEW else 1]
    check_payload_version(efi, row_id, meta, source)
    deps = read_json(relative_path(root, row['dependencies']))
    if row_id == 'igpu-only':
        require('systemSideNVIDIA' not in deps,
                'Disabled historical NVIDIA profile unexpectedly requires NVIDIA')
    else:
        require(deps['systemSideNVIDIA']['version'] == ('3.0' if row_id in NEW else '2.7.2'),
                'NVIDIA dependency version differs: ' + row_id)
    wex = [entry for entry in deps['components'] if entry['bundle'] == 'WhateverXe.kext']
    require(len(wex) == 1 and wex[0]['version'] == ('0.8.2' if row_id in NEW else '0.8.0'),
            'WEX dependency version differs: ' + row_id)
    # Included dependencies must match their profile payload, not merely a label.
    for entry in deps['components']:
        if entry.get('included'):
            check_files(relative_path(efi, 'OC/Kexts/' + entry['bundle']), entry['files'])
    return {'config': config, 'meta': meta, 'manifest': manifest, 'deps': deps, 'efi': efi}


def one_added(base, changed, label):
    remaining = list(changed)
    for entry in base:
        require(entry in remaining, 'USB experiment modifies existing ' + label)
        remaining.remove(entry)
    require(len(remaining) == 1 and len(changed) == len(base) + 1,
            'USB experiment must add exactly one ' + label)
    require(remaining[0].get('Enabled') is True, 'USB experiment addition is disabled: ' + label)
    return remaining[0]


def check_usb_delta(usable, diag):
    base = copy.deepcopy(usable['config'])
    experiment = copy.deepcopy(diag['config'])
    aml = one_added(base['ACPI']['Add'], experiment['ACPI']['Add'], 'ACPI/Add')
    one_added(base['ACPI']['Patch'], experiment['ACPI']['Patch'], 'ACPI/Patch')
    for key in ('Add', 'Patch'):
        experiment['ACPI'][key] = base['ACPI'][key]
    require(experiment == base, 'USB experiment changes non-USB config values')
    aml_name = 'OC/ACPI/' + aml['Path']
    require(aml_name.lower().endswith('.aml'), 'USB experiment addition is not AML')
    base_files, diag_files = usable['manifest'], diag['manifest']
    require(set(diag_files) - set(base_files) == {aml_name} and not set(base_files) - set(diag_files),
            'USB experiment payload adds more than one AML')
    for name in set(base_files) & set(diag_files) - {'OC/config.plist'}:
        require(base_files[name] == diag_files[name], 'USB experiment changes existing payload: ' + name)


def check_historical_tests(root, tests):
    require(tests['sameBootVerified'] is True and tests['allPassed'] is True, 'Historical test result is not PASS')
    require(tests['testCount'] == len(tests['cases']) == 7, 'Historical seven-case record differs')
    require(tests['NVIDIAHeadless'] is True and tests['NVIDIAVersion'] == '2.7.2' and
            tests['WEXVersion'] == '0.8.0 with R16 patches', 'Historical test cohort differs')
    require(tests['machineIdentityFieldsIncluded'] is False, 'Historical evidence includes identities')
    per_gpu_keys = {'requestedGPU', 'stage', 'test', 'passed', 'gpuWorkSubmitted', 'commandStatus',
                    'timedOut', 'mismatches', 'elementsChecked', 'pixelsChecked', 'shaderCompiled',
                    'shaderPipelineCreated', 'initialTextureBlueVerified'}
    queue_keys = {'test', 'passed', 'gpuWorkSubmitted', 'timedOut', 'crossGPUResources',
                  'hardwareExecutionOverlapMeasured', 'results'}
    result_keys = {'passed', 'lastResult', 'commandStatus', 'elementsChecked', 'tag',
                   'mismatches', 'expectedLastResult'}
    for case in tests['cases']:
        require(case['passed'] == 1 and case['gpuWorkSubmitted'] is True and case['timedOut'] == 0,
                'Historical GPU test failed')
        if 'results' in case:
            require(set(case) <= queue_keys and not case['crossGPUResources'] and
                    not case['hardwareExecutionOverlapMeasured'] and len(case['results']) == 2,
                    'Unexpected historical queue claim')
            for result in case['results']:
                require(set(result) <= result_keys and result['passed'] == 1 and
                        result['commandStatus'] == 4 and result['mismatches'] == 0 and
                        result['lastResult'] == result['expectedLastResult'], 'Historical queue result failed')
        else:
            require(set(case) <= per_gpu_keys and case['commandStatus'] == 4 and case['mismatches'] == 0,
                    'Historical per-GPU result failed')
    check_files(root / 'src/metal-smoke', tests['sourceFiles'])


def check_current_validation(validation):
    require(validation['WEXVersion'] == '0.8.2' and validation['NVIDIAVersion'] == '3.0',
            'Current validation cohort differs')
    intel = validation['intelCompute']
    require(intel['passed'] is True and intel['elementsChecked'] == 1024 and intel['mismatches'] == 0,
            'Current Intel 1024-element record differs')
    nvidia = validation['nvidiaModules']
    require(nvidia['loaded'] is True and nvidia['version'] == '3.0' and
            isinstance(nvidia['modules'], list) and len(nvidia['modules']) > 0 and
            all(isinstance(item, str) and item for item in nvidia['modules']),
            'Current NVIDIA module record differs')
    require(validation.get('sameBootSevenCasesVerified') is False,
            'Current evidence must not inherit historical seven-case proof')


def assembly_expected(deps):
    expected, unpinned = {}, []

    def add(name, record):
        if name in expected:
            require(expected[name] == {'bytes': record['bytes'], 'sha256': record['sha256']},
                    'Conflicting dependency record: ' + name)
        expected[name] = {'bytes': record['bytes'], 'sha256': record['sha256']}

    for component in deps['components']:
        if component.get('generatedLocally'):
            require(component.get('included') is False, 'Generated provider must not be published as included')
            unpinned.append(component['bundle'])
        for name, record in component.get('files', {}).items():
            add('OC/Kexts/' + component['bundle'] + '/' + name, record)
    for group, directory in (('externalUEFI', 'Drivers'), ('externalTools', 'Tools')):
        for entry in deps.get(group, []):
            add('OC/' + directory + '/' + entry['Path'], entry)
    for name, record in deps.get('resources', {}).get('files', {}).items():
        add('OC/Resources/' + name, record)
    return expected, unpinned


def verify(root, selected_id='current', assembled=None):
    catalog = read_json(root / 'profiles/catalog.json')
    require(catalog.get('schema') == 2, 'Profile catalog must use schema 2')
    rows = catalog['profiles']
    require(len(rows) == 6 and {row['id'] for row in rows} == ALL, 'Expected six unique profile rows')
    require(catalog.get('defaultProfile') == 'current', 'Default profile differs')
    for row in rows:
        require(all(isinstance(row.get(key), str) for key in ('efi', 'config', 'metadata', 'dependencies', 'manifest')),
                'Missing profile paths: ' + row['id'])
    sources = []
    for name in SOURCE_DIRS:
        source = read_json(root / name / 'source-manifest.json')
        check_files(root / name, source['files'], exact=True, exclusions=('source-manifest.json',))
        sources.append(source)
    require(sources[0]['binarySHA256'] != sources[1]['binarySHA256'], 'New and historical WEX snapshots are mixed')
    profiles = {row['id']: check_profile(root, row, sources) for row in rows}
    require(profiles['current']['config'] == profiles['usable-20261114']['config'],
            'Current and usable configuration differ')
    require(profiles['current']['manifest'] == profiles['usable-20261114']['manifest'],
            'Current and usable payload differ')
    check_usb_delta(profiles['usable-20261114'], profiles['usb-experimental'])
    # History is intentionally immutable: CPU cfg-lock and all other original
    # values are governed by their own manifests, not rewritten to new defaults.
    check_historical_tests(root, read_json(root / 'metadata/dual-gpu-tests.json'))
    check_current_validation(read_json(root / 'metadata/20261114/validation.json'))
    repository_manifest = read_json(root / 'metadata/repository-files.json')
    check_files(root, repository_manifest['files'], exact=True,
                exclusions=('metadata/repository-files.json',))
    print('PASS: six sanitized profiles; exact EFI/source/repository manifests; separate current and historical evidence.')
    print('Offline verification only. Current evidence is Intel 1024-element compute plus NVIDIA module loading; seven-case proof is historical.')
    if assembled is not None:
        selected = profiles[selected_id]
        # A user may have supplied their own SMBIOS in the assembled config.
        # Check published payloads without requiring the sanitized template.
        check_files(assembled, {name: record for name, record in selected['manifest'].items()
                                if name != 'OC/config.plist'})
        expected, unpinned = assembly_expected(selected['deps'])
        check_files(assembled, expected)
        print('PASS: known assembled EFI files match profile ' + selected_id + '.')
        if unpinned:
            print('Not hash-verified; generate and qualify locally: ' + ', '.join(unpinned))
        print('System-side Graphics/Compat/NVIDIA and personal SMBIOS are not verified. This is not a boot or complete-image certification.')
    else:
        print('Third-party and locally generated dependencies remain separate; the publication is not a complete boot image.')


def self_test():
    """Small owned fixtures, never full repository copies or active EFI writes."""
    config = {'PlatformInfo': {'Generic': {'MLB': '', 'SystemSerialNumber': '', 'SystemUUID': '', 'ROM': bytes(6)}},
              'Misc': {'Security': {'PasswordHash': b'', 'PasswordSalt': b''}},
              'NVRAM': {'Add': {GUID: {'boot-args': '-wex-r16-backlight64'}}}, 'Kernel': {'Add': []}}
    check_sanitized_config(config)
    rejected = []

    def reject(label, expected_message, operation):
        try:
            operation()
        except ValueError as error:
            require(expected_message in str(error), 'Wrong self-test failure: ' + str(error))
            rejected.append(label)
        else:
            raise ValueError('Self-test accepted invalid fixture: ' + label)

    with tempfile.TemporaryDirectory(prefix='r16-package-verifier-') as directory:
        root = Path(directory)
        original = root / 'original.plist'
        original.write_bytes(plistlib.dumps(config))
        altered = root / 'copy.plist'
        altered.write_bytes(original.read_bytes())
        private = plistlib.loads(altered.read_bytes())
        private['PlatformInfo']['Generic']['SystemSerialNumber'] = 'DO-NOT-PUBLISH'
        altered.write_bytes(plistlib.dumps(private))
        reject('nonempty-SMBIOS', 'Identity is not empty',
               lambda: check_sanitized_config(plistlib.loads(altered.read_bytes())))
        record = {'bytes': original.stat().st_size, 'sha256': digest(original)}
        check_files(root, {'original.plist': record})
        reject('manifest-traversal', 'Path outside package', lambda: check_files(root, {'../outside': record}))
        payload = root / 'efi'
        info = relative_path(payload, WEX + 'Info.plist')
        info.parent.mkdir(parents=True)
        binary = relative_path(payload, WEX + 'MacOS/WhateverXe')
        binary.parent.mkdir()
        binary.write_bytes(b'owned-test-fixture')
        info.write_bytes(plistlib.dumps({'CFBundleVersion': '0.8.2'}))
        meta = {'WhateverXeSHA256': digest(binary), 'NVIDIAVersion': '3.0'}
        source = {'binarySHA256': digest(binary)}
        check_payload_version(payload, 'current', meta, source)
        info.write_bytes(plistlib.dumps({'CFBundleVersion': '0.8.0'}))
        reject('mixed-WEX-cohort', 'Mixed WEX cohort', lambda: check_payload_version(payload, 'current', meta, source))
        info.write_bytes(plistlib.dumps({'CFBundleVersion': '0.8.2'}))
        binary.write_bytes(b'different-cohort-with-new-plist-label')
        reject('mislabeled-WEX-binary', 'WEX binary/source cohort differs',
               lambda: check_payload_version(payload, 'current', meta, source))
    print('PASS self-test: rejected ' + ', '.join(rejected) + '; valid owned fixtures accepted.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Published repository root (default: script parent)')
    parser.add_argument('--efi', type=Path, help='Also check known files in a separate, already assembled EFI')
    parser.add_argument('--profile', choices=sorted(ALL), default='current', help='Dependencies selected for --efi')
    parser.add_argument('--self-test', action='store_true', help='Run only small temporary positive/negative fixtures')
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
        else:
            verify(args.root.resolve(), args.profile, args.efi.resolve() if args.efi else None)
    except (ValueError, KeyError, TypeError, OSError, plistlib.InvalidFileException) as error:
        parser.exit(1, 'FAIL: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
