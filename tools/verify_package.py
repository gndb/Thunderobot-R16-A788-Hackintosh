"""Check the current EFI, its preserved rollback, source and public manifests offline."""
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
ALL = {'current', 'usable-20261114'}
WEX = 'OC/Kexts/WhateverXe.kext/Contents/'
SOURCE_DIR = 'src/WhateverXe'
SOURCE_COMMIT = '4512191b9643e2391431fbd9639305b61568ee32'
SOURCE_BINARY = '515f9399e72d7a761cd5bde32dfcb92d23be97e671f2d4ca5ec2ffa7db6a6d1a'
ARCHIVE_COMMIT = '5f8d2103d0674f057ef20e0acd65a85fa1ba7140'
ARCHIVE_TAG = 'archive/pre-cleanup-20261116'
HISTORICAL_BINARY = '7d7ee576fe84cc47919060a454d1b50bb718f54ee7b1872fb53fc20d2af2316a'
ARCHIVE_PATHS = {'profiles/historical-20261113', 'profiles/dual-gpu-verified-0527',
                 'profiles/igpu-only-20261113', 'profiles/experimental-usb-firmware-20261114',
                 'profiles/latest-20261116', 'src/WhateverXe-0.8.0-R16-historical'}
MAP = 'OC/Kexts/UTBMap.kext/Contents/Info.plist'
MAP_ID = 'com.nullmoth.UTBMap'
DIAGNOSTIC = 'OC/ACPI/SSDT-USB-RO-Diag.aml'
OWNER_CONFIG_SHA256 = 'bb7e1a098cf19f2d7f42339591a3fd7f7e4ac4b0f453801097cf9a7d87d8dd92'
DISABLED_BUNDLES = {'IOSkywalkFamily.kext', 'IO80211FamilyLegacy.kext',
                    'IO80211FamilyLegacy.kext/Contents/PlugIns/AirPortBrcmNIC.kext', 'WhateverGreen.kext'}
VISIBILITY = {'BOOT/.contentFlavour', 'BOOT/.contentVisibility', 'OC/.contentFlavour', 'OC/.contentVisibility'}
DIAGNOSTIC_RECORD = {'bytes': 666, 'sha256': '5ad6ff218a1d63ca9c8f7e4408d3aa8c246265c32ebdb5d8bff9dae4569513e4'}
AIRPORT_SOURCE = 'https://github.com/souissiak1-maker/AirportRTW/releases/tag/V2.3.3'
AIRPORT_FILES = {
    'Contents/Info.plist': {'bytes': 3174, 'sha256': '0f5dd64410925d385d9f65d87a700100c1e8c78a320641c4e8a3f0988e961294'},
    'Contents/MacOS/AirportRTW': {'bytes': 24244304, 'sha256': 'c63eee3bfd4a057c310a7ca6bc4a6fa4aeec8aabd79a851ab32532c5525ff201'},
    'Contents/Resources/LICENCE.rtlwifi_firmware.txt': {'bytes': 2086, 'sha256': 'f0f60e6d425b98fc1cb25eaf0668e3a3aa972c1b6b13d8cd1d365cd52d0c71d3'},
    'Contents/Resources/NOTICE.txt': {'bytes': 30931, 'sha256': '1a11e369362156a5c4206645d6ce5fe4ed7f7d98b0cb755a9433c249bf08c15e'},
}
PATCHES = {
    'patches/wex-0.8.2-r16/R16-on-WhateverXe-0.8.2-production.patch': 'e15f8a7f061c1f9bf63cf1e2cfc529fc06fa6bf75d46a49999b8db5b2e768f4e',
    'patches/wex-0.8.2-r16/R16-0.8.2-test-fixture-adaptation.patch': 'a121faa38b4da74e83cff85ec4d3a88339c4296d29540b735d3a6896e27fb968',
}


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
            all(x not in ('', '.', '..') for x in name.split('/')), 'Path outside package: ' + name)
    path = root.joinpath(*parts.parts)
    require(path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
            'Path outside package: ' + name)
    return path


def tree_files(root, exclusions=()):
    result = set()
    for path in root.rglob('*'):
        name = path.relative_to(root).as_posix()
        if (name.split('/')[0] == '.git' or name in exclusions or
                '__pycache__' in path.relative_to(root).parts or path.suffix == '.pyc'):
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
        require(isinstance(record, dict) and type(record.get('bytes')) is int and record['bytes'] >= 0 and
                isinstance(record.get('sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', record['sha256']),
                'Invalid manifest record: ' + name)
        require(path.is_file() and path.stat().st_size == record['bytes'] and digest(path) == record['sha256'],
                'Missing or changed file: ' + name)
    if exact:
        actual = tree_files(root, exclusions)
        require(actual == set(expected), 'Manifest tree differs; missing=%s extra=%s' %
                (sorted(set(expected) - actual), sorted(actual - set(expected))))


def check_sanitized_config(config):
    generic = config['PlatformInfo']['Generic']
    for key in ('MLB', 'SystemSerialNumber', 'SystemUUID'):
        require(generic.get(key) == '', 'Identity is not empty: ' + key)
    require(generic.get('ROM') == bytes(6), 'ROM must be six zero bytes')
    for key in ('PasswordHash', 'PasswordSalt'):
        require(key in config['Misc']['Security'] and config['Misc']['Security'][key] in (b'', ''),
                'Password field is not empty: ' + key)
    for branch in ('Add', 'Delete', 'LegacySchema'):
        for values in config.get('NVRAM', {}).get(branch, {}).values():
            keys = values.keys() if isinstance(values, dict) else values
            require(all('bluetooth' not in key.lower() for key in keys), 'Bluetooth NVRAM state remains')
    tokens = config['NVRAM']['Add'][GUID]['boot-args'].split()
    require('-wex-r16-backlight64' in tokens, 'Missing retained backlight64 opt-in')
    forbidden = ('-wex-r16-240hz', '-wex-r16-resume-r10', '-wex-r16-dim-r11')
    require(not any(token.startswith(forbidden) for token in tokens) and 'nmhybrid=1' not in tokens,
            'Disabled experimental display option is enabled')
    require('-nvoff' not in tokens, 'NVIDIA state differs from preserved dual-GPU cohort')
    require(all(entry['Enabled'] for entry in config['Kernel']['Add']), 'Disabled Kernel/Add entry remains')


def normalized_owner_config(config):
    """Normalize only the earlier publication edits for a functional comparison."""
    result = copy.deepcopy(config)
    generic = result['PlatformInfo']['Generic']
    for key in ('MLB', 'SystemSerialNumber', 'SystemUUID'):
        generic[key] = ''
    generic['ROM'] = bytes(6)
    for branch in ('Add', 'Delete', 'LegacySchema'):
        for guid, values in result.get('NVRAM', {}).get(branch, {}).items():
            if isinstance(values, dict):
                result['NVRAM'][branch][guid] = {key: value for key, value in values.items() if 'bluetooth' not in key.lower()}
            elif isinstance(values, list):
                values[:] = [key for key in values if 'bluetooth' not in key.lower()]
    disabled = [entry['BundlePath'] for entry in result['Kernel']['Add'] if not entry['Enabled']]
    require(len(disabled) == len(set(disabled)) and set(disabled) <= DISABLED_BUNDLES,
            'Unexpected disabled Kernel/Add entry in original config')
    result['Kernel']['Add'] = [entry for entry in result['Kernel']['Add'] if entry['Enabled']]
    return result


def check_owner_config(config, meta):
    check_current_metadata(meta)
    generic = config['PlatformInfo']['Generic']
    require(all(isinstance(generic.get(key), str) and generic[key] for key in ('MLB', 'SystemSerialNumber', 'SystemUUID')) and
            isinstance(generic.get('ROM'), bytes) and len(generic['ROM']) == 6,
            'Owner-approved original identity fields are absent or malformed')
    disabled = [entry['BundlePath'] for entry in config['Kernel']['Add'] if not entry['Enabled']]
    require(set(disabled) == DISABLED_BUNDLES and len(disabled) == 4, 'Original disabled-entry inventory differs')
    check_sanitized_config(normalized_owner_config(config))


def check_current_metadata(meta):
    require(meta.get('profile') == 'current' and meta.get('date') == '2026-11-16' and
            meta.get('scope') == '20261116-latest-deployment', 'Current metadata scope differs')
    require(meta.get('WEXVersion') == '0.8.2' and meta.get('NVIDIAVersion') == '3.0', 'Current version cohort differs')
    for key in ('runtimeVerified', 'sameBootSevenCasesVerified'):
        require(meta.get(key) is False, 'Current deployment must not claim runtime proof: ' + key)
    for key in ('desktopObserved', 'coldBootReliabilityVerified', 'displaySleepWakeResolved',
                'usbTypeCPDResolved', 'inheritsUsableSessionEvidence'):
        require(meta.get(key, False) is False, 'Current deployment inherits unverified success: ' + key)
    require(not {'intelCompute', 'nvidiaModulesLoaded', 'brightnessObserved'} & set(meta),
            'Current metadata must reference historical evidence separately')
    require(meta.get('sharedPayloadRoot') == 'EFI', 'Current payload path differs')
    require(meta.get('identityPublishedWithOwnerConsent') is True and
            meta.get('publicConfigHasMachineIdentity') is True, 'Original identity requires explicit owner consent')
    require(meta.get('fullEFIIncluded') is True and meta.get('assembledFullEFIIncluded') is True,
            'Current distribution must include the complete EFI file set')
    require(meta.get('publicConfigSHA256') == OWNER_CONFIG_SHA256, 'Owner-approved original config fingerprint differs')


def check_profile(root, row, source):
    row_id = row['id']
    require(row.get('expectedWEX') == '0.8.2' and row.get('expectedNVIDIA') == '3.0', 'Profile version labels differ')
    efi = relative_path(root, row['efi'])
    config_path = relative_path(root, row['config'])
    require(config_path == efi / 'OC/config.plist', 'Config is outside selected EFI')
    config = plistlib.loads(config_path.read_bytes())
    meta = read_json(relative_path(root, row['metadata']))
    if row_id == 'current':
        check_owner_config(config, meta)
    else:
        check_sanitized_config(config)
    require(meta.get('highRefreshEnabled') is False and
            meta.get('experimentalUSB') is (row_id == 'current'), 'Profile experiment scope differs')
    require(digest(config_path) == meta['publicConfigSHA256'], 'Public config hash differs')
    manifest = read_json(relative_path(root, row['manifest']))
    check_files(efi, manifest, exact=True)
    info = plistlib.loads(relative_path(efi, WEX + 'Info.plist').read_bytes())
    binary = digest(relative_path(efi, WEX + 'MacOS/WhateverXe'))
    require(info.get('CFBundleVersion') == '0.8.2' and binary == meta['WhateverXeSHA256'] == source['binarySHA256'] and
            meta['WEXVersion'] == '0.8.2' and meta['NVIDIAVersion'] == '3.0', 'WEX/binary/source cohort differs')
    deps = read_json(relative_path(root, row['dependencies']))
    require(deps['systemSideNVIDIA']['version'] == '3.0', 'NVIDIA dependency version differs')
    wex = [entry for entry in deps['components'] if entry['bundle'] == 'WhateverXe.kext']
    require(len(wex) == 1 and wex[0]['version'] == '0.8.2', 'WEX dependency version differs')
    for entry in deps['components']:
        if entry.get('included'):
            check_files(relative_path(efi, 'OC/Kexts/' + entry['bundle']), entry['files'])
    if row_id == 'current':
        check_current_metadata(meta)
    return {'config': config, 'meta': meta, 'manifest': manifest, 'deps': deps, 'efi': efi}


def one_added(base, changed, label):
    remaining = list(changed)
    for entry in base:
        require(entry in remaining, 'Current changes existing ' + label)
        remaining.remove(entry)
    require(len(remaining) == 1 and len(changed) == len(base) + 1 and remaining[0].get('Enabled') is True,
            'Current must add exactly one enabled ' + label)
    return remaining[0]


def check_current_map(data):
    info = plistlib.loads(data)
    require(info.get('CFBundleIdentifier') == MAP_ID, 'Current USB map bundle identifier differs')
    require(info.get('CFBundleVersion') == info.get('CFBundleShortVersionString') == '1.0.3', 'Current USB map version differs')
    personalities = info.get('IOKitPersonalities', {})
    require(isinstance(personalities, dict) and len(personalities) == 1, 'Current USB map must contain one controller')
    personality = next(iter(personalities.values()))
    require(personality.get('IOPCIPrimaryMatch', '').lower().split() == ['0x7a608086'], 'Current USB map controller differs')
    props = personality['IOProviderMergeProperties']
    ports = props['ports']
    expected = {'HS01': 1, 'HS02': 2, 'HS03': 3, 'HS04': 4, 'HS06': 6,
                'HS07': 7, 'SS01': 17, 'SS02': 18, 'SS03': 19, 'SS04': 20}
    require(isinstance(ports, dict) and set(ports) == set(expected), 'Current USB map must have exactly ten selected ports')
    require(props.get('port-count') == (20).to_bytes(4, 'little'), 'Current USB port-count differs')
    companions = {'HS02': 18, 'SS03': 1, 'HS03': 19, 'SS04': 2, 'HS04': 17, 'SS02': 3}
    for name, number in expected.items():
        port = ports[name]
        require(port.get('port') == number.to_bytes(4, 'little'), 'Current USB logical port differs: ' + name)
        connector = 9 if name in ('HS04', 'SS02') else 255 if name in ('HS06', 'HS07') else 3
        require(type(port.get('UsbConnector')) is int and port['UsbConnector'] == connector,
                'Current USB connector differs: ' + name)
        if 'usb-port-type' in port:
            require(type(port['usb-port-type']) is int and port['usb-port-type'] == connector,
                    'Current derived connector differs: ' + name)
        if name in companions:
            require(type(port.get('kUSBCompanionIndex')) is int and port['kUSBCompanionIndex'] == companions[name],
                    'Current USB companion differs: ' + name)


def component_index(deps):
    result = {}
    for component in deps['components']:
        bundle = component['bundle']
        require(bundle not in result, 'Duplicate dependency component: ' + bundle)
        result[bundle] = component
    return result


def check_current_delta(current, usable):
    check_current_metadata(current['meta'])
    base, changed = copy.deepcopy(usable['config']), normalized_owner_config(current['config'])
    aml = one_added(base['ACPI']['Add'], changed['ACPI']['Add'], 'ACPI/Add')
    one_added(base['ACPI']['Patch'], changed['ACPI']['Patch'], 'ACPI/Patch')
    for key in ('Add', 'Patch'):
        changed['ACPI'][key] = base['ACPI'][key]
    require(changed == base, 'Current changes unrelated config values')
    require('OC/ACPI/' + aml['Path'] == DIAGNOSTIC, 'Current adds an unexpected diagnostic AML')
    old_files, new_files = usable['manifest'], current['manifest']
    expected, _ = assembly_expected(current['deps'])
    allowed = set(expected) | set(old_files) | VISIBILITY | {DIAGNOSTIC}
    require(set(new_files) == allowed, 'Current complete EFI file set differs from configured payload')
    require(new_files[DIAGNOSTIC] == DIAGNOSTIC_RECORD, 'Current diagnostic AML fingerprint differs')
    for name in set(old_files) - {'OC/config.plist', MAP}:
        require(old_files[name] == new_files[name], 'Current changes an unrelated EFI payload: ' + name)
    for name, record in expected.items():
        require(new_files[name] == record, 'Current dependency payload fingerprint differs: ' + name)
    map_path = relative_path(current['efi'], MAP)
    check_current_map(map_path.read_bytes())
    require(current['meta'].get('USBMapVersion') == '1.0.3' and current['meta'].get('USBMapSHA256') == digest(map_path) and
            current['meta'].get('AirportRTWVersion') == '2.3.3', 'Current USB/Wi-Fi metadata differs')
    old, new = component_index(usable['deps']), component_index(current['deps'])
    require(set(old) == set(new), 'Current dependency component set differs')
    for bundle in set(old) - {'UTBMap.kext', 'AirportRTW.kext'}:
        previous = copy.deepcopy(old[bundle])
        actual = copy.deepcopy(new[bundle])
        previous.pop('included', None)
        actual.pop('included', None)
        if previous.get('generatedLocally'):
            provider_files = actual.pop('files')
            require(set(provider_files) == {'Contents/Info.plist'} and
                    provider_files['Contents/Info.plist']['sha256'] == previous['observedInfoSHA256'],
                    'Current locally generated provider fingerprint differs')
            previous.pop('files', None)
        require(previous == actual, 'Current changes an unrelated dependency: ' + bundle)
    require(all(item.get('included') is True for item in new.values()), 'Complete EFI must include every configured bundle')
    for bundle in ('UTBMap.kext', 'AirportRTW.kext'):
        permitted = {'version', 'files', 'source', 'included'} | ({'identifier'} if bundle == 'UTBMap.kext' else set())
        keep = lambda item: {key: value for key, value in item.items() if key not in permitted}
        require(keep(old[bundle]) == keep(new[bundle]), 'Current changes unrelated component fields: ' + bundle)
    utb, airport = new['UTBMap.kext'], new['AirportRTW.kext']
    require(utb['version'] == '1.0.3' and utb.get('identifier') == MAP_ID and utb.get('included') is True and
            utb.get('source') == old['UTBMap.kext'].get('source') and utb['files'] == {'Contents/Info.plist': new_files[MAP]},
            'Current USB dependency differs from public map')
    require(airport['version'] == '2.3.3' and airport.get('included') is True and
            airport.get('source') == AIRPORT_SOURCE and airport.get('files') == AIRPORT_FILES,
            'Current AirportRTW dependency differs from official 2.3.3')
    require(current['deps'].get('profile') == 'current', 'Current dependency profile differs')
    ignored = {'profile', 'components', 'resources', 'assembledFullEFIIncluded', 'identityMustBeGeneratedLocally',
               'identityPublishedWithOwnerConsent'}
    keep = lambda item: {key: value for key, value in item.items() if key not in ignored}
    expected_groups = copy.deepcopy(keep(usable['deps']))
    expected_groups['systemSideNVIDIA'].pop('runtimeLoadedModules', None)
    expected_groups['systemSideNVIDIA']['runtimeVerifiedForThisSnapshot'] = False
    require(current['deps']['systemSideNVIDIA'].get('runtimeVerifiedForThisSnapshot') is False and
            keep(current['deps']) == expected_groups, 'Current changes unrelated dependency groups')
    old_resources = usable['deps'].get('resources', {}).get('files', {})
    resources = current['deps'].get('resources', {}).get('files', {})
    require(all(resources.get(name) == record for name, record in old_resources.items()), 'Current changes existing resources')
    require(all(name.startswith('Image/R16/Minimal/') and name.endswith('.icns') for name in set(resources) - set(old_resources)),
            'Current adds unexpected theme resources')
    require(current['deps'].get('assembledFullEFIIncluded') is True and
            current['deps'].get('identityMustBeGeneratedLocally') is False and
            current['deps'].get('identityPublishedWithOwnerConsent') is True, 'Complete dependency publication scope differs')


def check_history(history):
    require(history.get('schema') == 1 and history.get('repository') == 'gndb/Thunderobot-R16-A788-Hackintosh' and
            history.get('archiveCommit') == ARCHIVE_COMMIT and history.get('archiveTag') == ARCHIVE_TAG,
            'Archive identity or immutable commit differs')
    require(isinstance(history.get('paths'), list) and len(history['paths']) == len(ARCHIVE_PATHS) and
            set(history['paths']) == ARCHIVE_PATHS, 'Archived path inventory differs')
    cohort = history['historicalGPU']
    require(cohort.get('WEXVersion') == '0.8.0' and cohort.get('NVIDIAVersion') == '2.7.2' and
            cohort.get('binarySHA256') == HISTORICAL_BINARY != SOURCE_BINARY, 'Historical GPU cohort differs')


def check_source(root):
    directory = root / SOURCE_DIR
    source = read_json(directory / 'source-manifest.json')
    require(source['baseCommit'] == SOURCE_COMMIT and source['binarySHA256'] == SOURCE_BINARY,
            'Current source/binary identity differs')
    require(source.get('sameBinaryRebuildPerformed') is False and source.get('sameBuildInputManifestLocated') is False,
            'Source reconstruction is mislabeled as a matched rebuild')
    check_files(directory, source['files'], exact=True, exclusions=('source-manifest.json',))
    provenance = read_json(root / 'metadata/source-provenance.json')
    require(provenance.get('sourceManifest') == SOURCE_DIR + '/source-manifest.json' and
            provenance.get('baseCommit') == SOURCE_COMMIT and provenance.get('binarySHA256') == SOURCE_BINARY,
            'Source provenance differs')
    archived = provenance.get('archivedSourceManifest', '')
    require(ARCHIVE_COMMIT in archived and archived.startswith('https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/') and
            archived.endswith('/src/WhateverXe-0.8.0-R16-historical/source-manifest.json'), 'Archived source reference differs')
    require('historicalSourceManifest' not in provenance, 'Deleted local historical source path remains')
    require(len(provenance['patches']) == len(PATCHES) and
            {entry['path']: entry['sha256'] for entry in provenance['patches']} == PATCHES, 'Source patch inventory differs')
    for name, expected in PATCHES.items():
        require(digest(relative_path(root, name)) == expected, 'Source patch fingerprint differs: ' + name)
    return source


def check_historical_tests(root, tests):
    require(tests['sameBootVerified'] is True and tests['allPassed'] is True, 'Historical test result is not PASS')
    require(tests['testCount'] == len(tests['cases']) == 7, 'Historical seven-case record differs')
    require(tests['NVIDIAHeadless'] is True and tests['NVIDIAVersion'] == '2.7.2' and
            tests['WEXVersion'] == '0.8.0 with R16 patches' and tests['machineIdentityFieldsIncluded'] is False,
            'Historical test cohort or identity scope differs')
    per_gpu_keys = {'requestedGPU', 'stage', 'test', 'passed', 'gpuWorkSubmitted', 'commandStatus',
                    'timedOut', 'mismatches', 'elementsChecked', 'pixelsChecked', 'shaderCompiled',
                    'shaderPipelineCreated', 'initialTextureBlueVerified'}
    queue_keys = {'test', 'passed', 'gpuWorkSubmitted', 'timedOut', 'crossGPUResources',
                  'hardwareExecutionOverlapMeasured', 'results'}
    result_keys = {'passed', 'lastResult', 'commandStatus', 'elementsChecked', 'tag', 'mismatches', 'expectedLastResult'}
    for case in tests['cases']:
        require(case['passed'] == 1 and case['gpuWorkSubmitted'] is True and case['timedOut'] == 0,
                'Historical GPU test failed')
        if 'results' in case:
            require(set(case) <= queue_keys and not case['crossGPUResources'] and
                    not case['hardwareExecutionOverlapMeasured'] and len(case['results']) == 2,
                    'Unexpected historical queue claim')
            for result in case['results']:
                require(set(result) <= result_keys and result['passed'] == 1 and result['commandStatus'] == 4 and
                        result['mismatches'] == 0 and result['lastResult'] == result['expectedLastResult'],
                        'Historical queue result failed')
        else:
            require(set(case) <= per_gpu_keys and case['commandStatus'] == 4 and case['mismatches'] == 0,
                    'Historical per-GPU result failed')
    check_files(root / 'src/metal-smoke', tests['sourceFiles'])


def check_success_validation(validation):
    require(validation['WEXVersion'] == '0.8.2' and validation['NVIDIAVersion'] == '3.0', 'Success-session cohort differs')
    intel, nvidia = validation['intelCompute'], validation['nvidiaModules']
    require(intel['passed'] is True and intel['elementsChecked'] == 1024 and intel['mismatches'] == 0,
            'Success-session Intel record differs')
    require(nvidia['loaded'] is True and nvidia['version'] == '3.0' and isinstance(nvidia['modules'], list) and
            len(nvidia['modules']) > 0 and all(isinstance(item, str) and item for item in nvidia['modules']),
            'Success-session NVIDIA module record differs')
    require(validation.get('sameBootSevenCasesVerified') is False, 'Success-session inherits historical seven-case proof')


def assembly_expected(deps):
    expected, unpinned = {}, []
    def add(name, record):
        value = {'bytes': record['bytes'], 'sha256': record['sha256']}
        require(name not in expected or expected[name] == value, 'Conflicting dependency record: ' + name)
        expected[name] = value
    for component in deps['components']:
        if component.get('generatedLocally') and not component.get('files'):
            unpinned.append(component['bundle'])
        for name, record in component.get('files', {}).items():
            add('OC/Kexts/' + component['bundle'] + '/' + name, record)
    for group, directory in (('externalUEFI', 'Drivers'), ('externalTools', 'Tools')):
        for entry in deps.get(group, []):
            add('OC/' + directory + '/' + entry['Path'], entry)
    for name, record in deps.get('resources', {}).get('files', {}).items():
        add('OC/Resources/' + name, record)
    return expected, unpinned


def check_assembly_catalog(root, current):
    full = read_json(root / 'metadata/assembly-manifest.json')
    require(full.get('schema') == 1 and full.get('profile') == 'current' and
            full.get('runtimeVerifiedForThisRevision') is False, 'Full assembly scope differs')
    files = full['files']
    require(full.get('fullEFIFileCount') == len(files) == 179, 'Full assembly file count differs')
    require(files == current['manifest'], 'Complete assembly manifest differs from the published EFI')
    expected, _ = assembly_expected(current['deps'])
    require(set(expected) <= set(files), 'Full assembly omits configured dependencies')
    for name, record in files.items():
        relative_path(root / 'EFI', name)
        require(type(record.get('bytes')) is int and record['bytes'] >= 0 and
                re.fullmatch(r'[0-9a-f]{64}', record.get('sha256', '')) is not None,
                'Invalid full assembly record: ' + name)
        require('config.plist.' not in name and '.kext.nullmoth-' not in name,
                'Inactive backup in full assembly: ' + name)
        if name in expected:
            require(record == expected[name], 'Full assembly dependency fingerprint differs: ' + name)
    provider = 'OC/Kexts/CPUFriendDataProvider.kext/Contents/Info.plist'
    observed = next(item for item in current['deps']['components'] if item['bundle'] == 'CPUFriendDataProvider.kext')
    require(files[provider]['sha256'] == observed['observedInfoSHA256'], 'Full assembly power data differs')
    public = read_json(root / 'metadata/distribution.json')
    require(public.get('schema') == 1 and public.get('profile') == 'current' and
            public.get('completeBootImage') is True and public.get('identityMustBeGeneratedLocally') is False and
            public.get('identityPublishedWithOwnerConsent') is True, 'Complete distribution scope differs')
    require(public.get('completeEFIRequiredFiles') == len(files) and
            public.get('publicExpandedEFIFileCount') == len(public['files']) == 179,
            'Complete distribution count differs')
    require(public['files'] == files, 'Complete distribution fingerprint differs')
    for source in public.get('sourceAssets', []):
        require(re.fullmatch(r'[0-9a-f]{40}', source.get('commit', '')) is not None and
                re.fullmatch(r'[0-9a-f]{64}', source.get('sha256', '')) is not None and
                source.get('upstreamURL', '').startswith('https://codeload.github.com/'),
                'Invalid corresponding source archive')


def verify(root, selected_id='current', assembled=None):
    catalog = read_json(root / 'profiles/catalog.json')
    rows = catalog['profiles']
    require(catalog.get('schema') == 2 and catalog.get('defaultProfile') == 'current' and
            len(rows) == 2 and {row['id'] for row in rows} == ALL, 'Expected current and one preserved rollback profile')
    for row in rows:
        prefix = '' if row['id'] == 'current' else 'profiles/usable-20261114/'
        expected = {'efi': prefix + 'EFI', 'config': prefix + 'EFI/OC/config.plist',
                    'metadata': 'metadata/current.json' if not prefix else prefix + 'metadata.json',
                    'dependencies': 'metadata/dependencies.json' if not prefix else prefix + 'dependencies.json',
                    'manifest': 'metadata/efi-manifest.json' if not prefix else prefix + 'efi-manifest.json'}
        require(all(row.get(key) == value for key, value in expected.items()), 'Profile entry point differs: ' + row['id'])
    source = check_source(root)
    profiles = {row['id']: check_profile(root, row, source) for row in rows}
    check_current_delta(profiles['current'], profiles['usable-20261114'])
    check_history(read_json(root / 'metadata/history.json'))
    check_historical_tests(root, read_json(root / 'metadata/dual-gpu-tests.json'))
    check_success_validation(read_json(root / 'metadata/validation-20261114.json'))
    check_assembly_catalog(root, profiles['current'])
    check_files(root, read_json(root / 'metadata/repository-files.json')['files'], exact=True,
                exclusions=('metadata/repository-files.json',))
    print('PASS: current EFI, preserved rollback, USB pairing, dependency delta, source and exact manifests.')
    print('Archived cohorts are pinned by commit; historical test records are checked separately. No new boot or PD repair is certified.')
    if assembled is not None:
        selected = profiles[selected_id]
        check_files(assembled, {name: record for name, record in selected['manifest'].items() if name != 'OC/config.plist'})
        expected, unpinned = assembly_expected(selected['deps'])
        check_files(assembled, expected)
        print('PASS: known assembled EFI files match profile ' + selected_id + '.')
        if unpinned:
            print('Not hash-verified; generate and qualify locally: ' + ', '.join(unpinned))
        print('System-side graphics, SMBIOS and actual hardware behavior remain outside this check.')
    else:
        print('PASS: complete 179-file EFI is published with the owner-approved original config; backups are excluded.')


def self_test():
    rejected = []
    def reject(name, fragment, action):
        try:
            action()
        except ValueError as error:
            require(fragment in str(error), 'Wrong rejection for ' + name + ': ' + str(error))
            rejected.append(name)
        else:
            raise ValueError('Invalid fixture accepted: ' + name)
    config = {'PlatformInfo': {'Generic': {'MLB': '', 'SystemSerialNumber': '', 'SystemUUID': '', 'ROM': bytes(6)}},
              'Misc': {'Security': {'PasswordHash': b'', 'PasswordSalt': b''}},
              'NVRAM': {'Add': {GUID: {'boot-args': '-wex-r16-backlight64'}}},
              'Kernel': {'Add': []}, 'ACPI': {'Add': [], 'Patch': []}}
    check_sanitized_config(config)
    bad = copy.deepcopy(config)
    bad['PlatformInfo']['Generic']['SystemSerialNumber'] = 'OWNED-TEST-ID'
    reject('nonempty-identity', 'Identity is not empty', lambda: check_sanitized_config(bad))
    meta = {'profile': 'current', 'date': '2026-11-16', 'scope': '20261116-latest-deployment',
            'WEXVersion': '0.8.2', 'NVIDIAVersion': '3.0', 'runtimeVerified': False,
            'sameBootSevenCasesVerified': False, 'assembledFullEFIIncluded': True, 'fullEFIIncluded': True,
            'identityPublishedWithOwnerConsent': True, 'publicConfigHasMachineIdentity': True,
            'publicConfigSHA256': OWNER_CONFIG_SHA256, 'sharedPayloadRoot': 'EFI'}
    check_current_metadata(meta)
    reject('owner-consent-missing', 'explicit owner consent', lambda: check_current_metadata(dict(meta, identityPublishedWithOwnerConsent=False)))
    reject('runtime-overclaim', 'must not claim runtime proof', lambda: check_current_metadata(dict(meta, runtimeVerified=True)))
    reject('borrowed-Intel-proof', 'historical evidence separately', lambda: check_current_metadata(dict(meta, intelCompute={'passed': True})))
    history = {'schema': 1, 'repository': 'gndb/Thunderobot-R16-A788-Hackintosh', 'archiveCommit': ARCHIVE_COMMIT,
               'archiveTag': ARCHIVE_TAG, 'paths': sorted(ARCHIVE_PATHS),
               'historicalGPU': {'WEXVersion': '0.8.0', 'NVIDIAVersion': '2.7.2', 'binarySHA256': HISTORICAL_BINARY}}
    check_history(history)
    reject('unfixed-archive-ref', 'Archive identity', lambda: check_history(dict(history, archiveCommit='main')))
    bad_history = copy.deepcopy(history)
    bad_history['historicalGPU']['WEXVersion'] = '0.8.2'
    reject('historical-cohort-mix', 'Historical GPU cohort', lambda: check_history(bad_history))
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        reject('manifest-traversal', 'Path outside package', lambda: relative_path(root, '../escape'))
        expected = {'HS01': 1, 'HS02': 2, 'HS03': 3, 'HS04': 4, 'HS06': 6,
                    'HS07': 7, 'SS01': 17, 'SS02': 18, 'SS03': 19, 'SS04': 20}
        companions = {'HS02': 18, 'SS03': 1, 'HS03': 19, 'SS04': 2, 'HS04': 17, 'SS02': 3}
        ports = {name: {'port': number.to_bytes(4, 'little'),
                       'UsbConnector': 9 if name in ('HS04', 'SS02') else 255 if name in ('HS06', 'HS07') else 3}
                 for name, number in expected.items()}
        for name, number in companions.items():
            ports[name]['kUSBCompanionIndex'] = number
        usb_map = {'CFBundleIdentifier': MAP_ID, 'CFBundleVersion': '1.0.3', 'CFBundleShortVersionString': '1.0.3',
                   'IOKitPersonalities': {'Controller': {'IOPCIPrimaryMatch': '0x7A608086',
                    'IOProviderMergeProperties': {'port-count': (20).to_bytes(4, 'little'), 'ports': ports}}}}
        check_current_map(plistlib.dumps(usb_map))
        for name, fragment, mutate in (
            ('wrong-map-id', 'bundle identifier', lambda m: m.update(CFBundleIdentifier='wrong')),
            ('wrong-map-version', 'map version', lambda m: m.update(CFBundleVersion='1.1')),
            ('wrong-TypeC-companion', 'companion differs', lambda m: m['IOKitPersonalities']['Controller']['IOProviderMergeProperties']['ports']['HS04'].update(kUSBCompanionIndex=1)),
            ('reintroduced-HS15', 'exactly ten', lambda m: m['IOKitPersonalities']['Controller']['IOProviderMergeProperties']['ports'].update(HS15={'port': bytes(4)})),
            ('wrong-internal-connector', 'connector differs', lambda m: m['IOKitPersonalities']['Controller']['IOProviderMergeProperties']['ports']['HS06'].update(UsbConnector=3)),
        ):
            changed = copy.deepcopy(usb_map)
            mutate(changed)
            reject(name, fragment, lambda: check_current_map(plistlib.dumps(changed)))
        efi = root / 'EFI'
        map_path = efi / MAP
        map_path.parent.mkdir(parents=True)
        map_path.write_bytes(plistlib.dumps(usb_map))
        map_record = {'bytes': map_path.stat().st_size, 'sha256': digest(map_path)}
        meta.update(USBMapVersion='1.0.3', USBMapSHA256=map_record['sha256'], AirportRTWVersion='2.3.3')
        old_components = [{'bundle': 'UTBMap.kext', 'identifier': 'com.dhinakg.USBToolBox.map', 'version': '1.1', 'included': True, 'files': {}, 'source': 'local'},
                          {'bundle': 'AirportRTW.kext', 'version': '2.3.1', 'included': False, 'files': {}, 'source': 'historical'},
                          {'bundle': 'owned.kext', 'version': '1.0', 'included': False}]
        usable = {'config': copy.deepcopy(config), 'manifest': {MAP: {}, 'OC/config.plist': {}, 'OC/OpenCore.efi': {'owned': True}},
                  'deps': {'profile': 'usable-20261114', 'components': old_components,
                           'systemSideNVIDIA': {'version': '3.0', 'runtimeLoadedModules': ['owned']}}}
        current = copy.deepcopy(usable)
        current.update(efi=efi, meta=meta)
        current['config']['ACPI']['Add'] = [{'Enabled': True, 'Path': 'SSDT-USB-RO-Diag.aml'}]
        current['config']['ACPI']['Patch'] = [{'Enabled': True, 'owned': 'patch'}]
        current['manifest'].update({MAP: map_record, DIAGNOSTIC: copy.deepcopy(DIAGNOSTIC_RECORD)})
        current['deps']['profile'] = 'current'
        current['deps']['components'][0].update(identifier=MAP_ID, version='1.0.3', files={'Contents/Info.plist': map_record})
        current['deps']['components'][1].update(version='2.3.3', source=AIRPORT_SOURCE, files=copy.deepcopy(AIRPORT_FILES))
        for component in current['deps']['components']: component['included'] = True
        current['deps']['assembledFullEFIIncluded'] = True
        current['deps']['identityMustBeGeneratedLocally'] = False
        current['deps']['identityPublishedWithOwnerConsent'] = True
        required, _ = assembly_expected(current['deps'])
        current['manifest'].update(required)
        for name in VISIBILITY: current['manifest'][name] = {'bytes': 0, 'sha256': '0' * 64}
        current['deps']['systemSideNVIDIA'] = {'version': '3.0', 'runtimeVerifiedForThisSnapshot': False}
        check_current_delta(current, usable)
        for name, fragment, mutate in (
            ('unrelated-config-change', 'unrelated config', lambda m: m['config'].update(owned='changed')),
            ('extra-ACPI-addition', 'exactly one', lambda m: m['config']['ACPI']['Add'].append({'Enabled': True, 'Path': 'extra.aml'})),
            ('unrelated-payload-change', 'unrelated EFI payload', lambda m: m['manifest']['OC/OpenCore.efi'].update(owned=False)),
            ('extra-public-payload', 'file set differs', lambda m: m['manifest'].update({'OC/Kexts/opaque': {}})),
            ('wrong-diagnostic-AML', 'diagnostic AML fingerprint', lambda m: m['manifest'][DIAGNOSTIC].update(sha256='0' * 64)),
            ('wrong-Airport-dependency', 'dependency payload fingerprint', lambda m: m['deps']['components'][1]['files']['Contents/Info.plist'].update(sha256='0' * 64)),
            ('unrelated-dependency-change', 'unrelated dependency', lambda m: m['deps']['components'][2].update(version='2.0')),
        ):
            changed = copy.deepcopy(current)
            mutate(changed)
            reject(name, fragment, lambda: check_current_delta(changed, usable))
    print('PASS self-test: %d invalid fixtures rejected; valid owned fixtures accepted.' % len(rejected))
    print(', '.join(rejected))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--efi', type=Path, help='Check known files in a separate, assembled EFI')
    parser.add_argument('--profile', choices=sorted(ALL), default='current')
    parser.add_argument('--self-test', action='store_true')
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
