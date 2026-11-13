"""Verify public profile integrity, empty machine identities and evidence scope."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import plistlib

ROOT = Path(__file__).resolve().parents[1]
GUID = '7C436110-AB2A-4BBB-A880-FE41995C9F82'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_files(root, expected):
    for name, record in expected.items():
        p = root/name
        assert p.resolve().is_relative_to(root.resolve()), 'Path outside package'
        assert p.is_file(), 'Missing: '+name
        assert p.stat().st_size == record['bytes'] and digest(p) == record['sha256'], 'Hash mismatch: '+name


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def check_profile(row):
    path = ROOT/row['config']
    c = plistlib.loads(path.read_bytes())
    meta = read_json(ROOT/row['metadata'])
    generic = c['PlatformInfo']['Generic']
    assert all(not generic.get(k) for k in ['MLB', 'SystemSerialNumber', 'SystemUUID'])
    assert generic['ROM'] == bytes(6)
    assert not c['NVRAM']['Add'][GUID].get('bluetoothInternalControllerInfo')
    tokens = c['NVRAM']['Add'][GUID]['boot-args'].split()
    assert '-wex-r16-backlight64' in tokens
    assert not any(x in tokens for x in ['-wex-r16-240hz', '-wex-r16-240hz-qhd-dsc',
        '-wex-r16-resume-r10', '-wex-r16-dim-r11', 'nmhybrid=1'])
    assert ('-nvoff' in tokens) == (row['id'] == 'igpu-only')
    assert not meta['highRefreshEnabled']
    assert digest(path) == meta['publicConfigSHA256']
    assert all(x['Enabled'] for x in c['Kernel']['Add'])
    return c


def check_tests(tests):
    assert tests['sameBootVerified'] and tests['allPassed']
    assert tests['testCount'] == len(tests['cases']) == 7
    assert tests['NVIDIAHeadless'] and tests['NVIDIAVersion'] == '2.7.2'
    assert not tests['machineIdentityFieldsIncluded']
    per_gpu_keys = {'requestedGPU', 'stage', 'test', 'passed', 'gpuWorkSubmitted', 'commandStatus',
        'timedOut', 'mismatches', 'elementsChecked', 'pixelsChecked', 'shaderCompiled',
        'shaderPipelineCreated', 'initialTextureBlueVerified'}
    queue_keys = {'test', 'passed', 'gpuWorkSubmitted', 'timedOut', 'crossGPUResources',
        'hardwareExecutionOverlapMeasured', 'results'}
    queue_result_keys = {'passed', 'lastResult', 'commandStatus', 'elementsChecked', 'tag',
        'mismatches', 'expectedLastResult'}
    for case in tests['cases']:
        assert case['passed'] and case['gpuWorkSubmitted'] and case['timedOut'] == 0
        if 'results' in case:
            assert set(case) <= queue_keys
            assert not case['crossGPUResources'] and not case['hardwareExecutionOverlapMeasured']
            assert len(case['results']) == 2
            for result in case['results']:
                assert set(result) <= queue_result_keys
                assert result['passed'] and result['commandStatus'] == 4 and result['mismatches'] == 0
                assert result['lastResult'] == result['expectedLastResult']
        else:
            assert set(case) <= per_gpu_keys
            assert case['commandStatus'] == 4 and case['mismatches'] == 0
    check_files(ROOT/'src/metal-smoke', tests['sourceFiles'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--efi', type=Path, help='Also check third-party files in a separately assembled full EFI')
    parser.add_argument('--profile', choices=['current', 'dual-tested', 'igpu-only'], default='current',
                        help='Select dependencies for --efi; all public configs are always checked')
    args = parser.parse_args()
    baseline = json.loads((ROOT/'metadata/baseline.json').read_text(encoding='utf-8'))
    public = json.loads((ROOT/'metadata/efi-manifest.json').read_text(encoding='utf-8'))
    source = json.loads((ROOT/'src/WhateverXe/source-manifest.json').read_text(encoding='utf-8'))
    check_files(ROOT/'EFI', public)
    check_files(ROOT/'src/WhateverXe', source['files'])
    catalog = read_json(ROOT/'profiles/catalog.json')
    configs = {row['id']: check_profile(row) for row in catalog['profiles']}
    assert set(configs) == {'current', 'dual-tested', 'igpu-only'}
    assert baseline['hybridNVIDIAChangeHardwareVerified'] and baseline['NVIDIAVersion'] == '2.7.2'
    assert not baseline['version2_9Installed'] and not baseline['currentNetworkDriverRuntimeVerified']
    assert not baseline['completeCurrentProfileHardwareVerified']
    current = copy.deepcopy(configs['current'])
    tested = configs['dual-tested']
    args_tested = tested['NVRAM']['Add'][GUID]['boot-args'].split()
    assert '-v' in args_tested
    assert current['NVRAM']['Add'][GUID]['boot-args'].split() == [x for x in args_tested if x != '-v']
    current['NVRAM']['Add'][GUID]['boot-args'] = tested['NVRAM']['Add'][GUID]['boot-args']
    assert current == tested, 'Unexpected config change since successful dual-GPU session'
    assert digest(ROOT/'EFI/OC/Kexts/WhateverXe.kext/Contents/MacOS/WhateverXe') == baseline['WhateverXeSHA256'] == source['binarySHA256']
    assert not list((ROOT/'EFI/OC').glob('config.*.plist'))
    assert not list((ROOT/'EFI/OC/Kexts').glob('WhateverXe.before-*'))
    check_tests(read_json(ROOT/'metadata/dual-gpu-tests.json'))
    print('PASS: three sanitized profiles, EFI/source hashes, profile differences and seven test records.')
    print('This is offline package verification; hardware boot and stability are not tested by this script.')
    if args.efi:
        selected = next(row for row in catalog['profiles'] if row['id'] == args.profile)
        deps = read_json(ROOT/selected['dependencies'])
        expected = {}
        for component in deps['components']:
            for name, record in component['files'].items():
                expected['OC/Kexts/'+component['bundle']+'/'+name] = record
        for row in deps['externalUEFI']:
            expected['OC/Drivers/'+row['Path']] = row
        for row in deps['externalTools']:
            expected['OC/Tools/'+row['Path']] = row
        expected.update({'OC/Resources/'+name:record for name,record in deps['resources']['files'].items()})
        check_files(args.efi,expected)
        print('PASS: separately assembled third-party EFI files match profile '+args.profile+'.')
        print('System-side Graphics/Compat/NVIDIA dependencies are not checked by --efi.')
    else:
        print('Third-party dependencies and personal SMBIOS still need to be supplied; this is not a complete boot image.')


if __name__ == '__main__':
    main()
