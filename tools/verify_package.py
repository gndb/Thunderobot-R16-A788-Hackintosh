"""Verify publication integrity, empty machine identities and baseline scope."""
from pathlib import Path
import argparse
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--efi', type=Path, help='Also check third-party files in a separately assembled full EFI')
    args = parser.parse_args()
    baseline = json.loads((ROOT/'metadata/baseline.json').read_text(encoding='utf-8'))
    public = json.loads((ROOT/'metadata/efi-manifest.json').read_text(encoding='utf-8'))
    source = json.loads((ROOT/'src/WhateverXe/source-manifest.json').read_text(encoding='utf-8'))
    check_files(ROOT/'EFI', public)
    check_files(ROOT/'src/WhateverXe', source['files'])
    c = plistlib.loads((ROOT/'EFI/OC/config.plist').read_bytes())
    generic = c['PlatformInfo']['Generic']
    assert all(not generic.get(k) for k in ['MLB','SystemSerialNumber','SystemUUID'])
    assert generic['ROM'] == bytes(6)
    assert not c['NVRAM']['Add'][GUID].get('bluetoothInternalControllerInfo')
    tokens = c['NVRAM']['Add'][GUID]['boot-args'].split()
    assert '-nvoff' in tokens and '-wex-r16-backlight64' in tokens
    assert not any(x in tokens for x in ['-wex-r16-240hz','-wex-r16-240hz-qhd-dsc','-wex-r16-resume-r10','-wex-r16-dim-r11'])
    assert not baseline['highRefreshEnabled'] and not baseline['hybridNVIDIAChangeHardwareVerified']
    assert digest(ROOT/'EFI/OC/config.plist') == baseline['publicConfigSHA256']
    assert digest(ROOT/'EFI/OC/Kexts/WhateverXe.kext/Contents/MacOS/WhateverXe') == baseline['WhateverXeSHA256'] == source['binarySHA256']
    assert all(x['Enabled'] for x in c['Kernel']['Add'])
    assert not list((ROOT/'EFI/OC').glob('config.*.plist'))
    assert not list((ROOT/'EFI/OC/Kexts').glob('WhateverXe.before-*'))
    print('PASS: public identities empty, EFI/source hashes match, high refresh off, successful baseline preserved.')
    print('This is offline package verification; hardware boot and stability are not tested by this script.')
    if args.efi:
        deps = json.loads((ROOT/'metadata/dependencies.json').read_text(encoding='utf-8'))
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
        print('PASS: separately assembled third-party files match the recorded baseline.')
    else:
        print('Third-party dependencies and personal SMBIOS still need to be supplied; this is not a complete boot image.')


if __name__ == '__main__':
    main()
