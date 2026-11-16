"""Build a sanitized current partial-EFI ZIP from the verified repository."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'https://github.com/gndb/Thunderobot-R16-A788-Hackintosh'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def markdown(path):
    """Keep links usable when a source document is placed elsewhere in the ZIP."""
    text = path.read_text(encoding='utf-8-sig')
    def replace(match):
        target = match.group(1)
        if target.startswith(('#', 'https://', 'http://', 'mailto:')):
            return match.group(0)
        name, separator, anchor = target.partition('#')
        resolved = (path.parent / name).resolve()
        if not resolved.is_relative_to(ROOT):
            raise ValueError('Document link escapes repository: ' + name)
        kind = 'tree' if resolved.is_dir() else 'blob'
        url = REPOSITORY + '/' + kind + '/main/' + urllib.parse.quote(resolved.relative_to(ROOT).as_posix())
        return '](' + url + (separator + anchor if separator else '') + ')'
    return re.sub(r'\]\(([^)]+)\)', replace, text).encode('utf-8')


def build(output):
    output = output.resolve()
    if output.is_relative_to(ROOT):
        raise ValueError('Release output must be outside the repository to preserve its exact manifest.')
    sys.dont_write_bytecode = True
    from verify_package import verify
    verify(ROOT, 'current')
    rows = read_json(ROOT / 'profiles/catalog.json')['profiles']
    row = next(item for item in rows if item['id'] == 'current')
    manifest = read_json(ROOT / row['manifest'])
    meta = read_json(ROOT / row['metadata'])
    assert meta['runtimeVerified'] is False and meta['assembledFullEFIIncluded'] is False
    data = {}
    for name, record in manifest.items():
        payload = (ROOT / row['efi'] / name).read_bytes()
        assert len(payload) == record['bytes'] and sha(payload) == record['sha256']
        data['EFI/' + name] = payload
    for source, target in (
        (row['metadata'], 'metadata/profile.json'),
        (row['dependencies'], 'metadata/dependencies.json'),
        (row['manifest'], 'metadata/efi-manifest.json'),
        ('metadata/history.json', 'metadata/history.json'),
        ('metadata/source-provenance.json', 'source/provenance.json'),
        ('src/WhateverXe/source-manifest.json', 'source/WEX-source-manifest.json'),
        ('LICENSE', 'LICENSE'),
        ('licenses/OpenCore-BSD-3-Clause.txt', 'licenses/OpenCore-BSD-3-Clause.txt'),
        ('licenses/WhateverXe-BSD-3-Clause.txt', 'licenses/WhateverXe-BSD-3-Clause.txt'),
    ):
        data[target] = (ROOT / source).read_bytes()
    for name in ('INSTALL', 'HISTORY', 'STATUS', 'DEVELOPMENT', 'THIRD_PARTY', 'HARDWARE'):
        data['docs/' + name + '.md'] = markdown(ROOT / 'docs' / (name + '.md'))
    data['docs/PROFILE.md'] = markdown(ROOT / 'README.md')
    data['docs/USB-TYPEC.md'] = markdown(ROOT / 'docs/issues/usb-typec.md')
    release = {'schema': 2, 'profile': 'current', 'date': meta['date'],
               'completeBootImage': False, 'runtimeVerified': False, 'experimentalUSB': True,
               'highRefreshEnabled': False, 'publicEFIFileCount': len(manifest),
               'sourceRepository': REPOSITORY, 'sourceProfile': 'EFI',
               'identityMustBeGeneratedLocally': True}
    data['release.json'] = (json.dumps(release, indent=2) + '\n').encode()
    lines = [
        '# R16 A788: current partial EFI', '',
        'Sanitized configuration and permitted payloads; this is not a complete boot image.',
        'Current: WEX 0.8.2-R16, UTBMap 1.0.3, HS04/SS02 pairing. High refresh remains disabled.',
        'AirportRTW 2.3.3 is an external dependency, not bundled.',
        'The current USB revision has no completed runtime acceptance record. USB-C/PD and display recovery remain unresolved.', '',
        'Use metadata/dependencies.json for exact versions and hashes. Supply the missing drivers,',
        'your own SMBIOS identity, and locally generated CPUFriend data. Install system-side graphics separately.',
        'See docs/INSTALL.md and docs/USB-TYPEC.md. Documentation links point to the source repository.', '',
        'The known-success rollback remains in profiles/usable-20261114 in the repository.',
        'Older payloads and reports are pinned by metadata/history.json; historical results do not validate the current snapshot.', '',
        REPOSITORY,
    ]
    data['README.md'] = ('\n'.join(lines) + '\n').encode()
    index = {name: {'bytes': len(payload), 'sha256': sha(payload)} for name, payload in sorted(data.items())}
    data['file-manifest.json'] = (json.dumps(index, indent=2) + '\n').encode()
    output.mkdir(parents=True, exist_ok=True)
    target = output / ('R16-A788-current-' + meta['date'].replace('-', '') + '-partial-EFI.zip')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, payload in sorted(data.items()):
            info = zipfile.ZipInfo(name, (2026, 11, 16, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(set(archive.namelist()))
        assert set(archive.namelist()) == set(data)
        for name, record in index.items():
            payload = archive.read(name)
            assert len(payload) == record['bytes'] and sha(payload) == record['sha256']
    checksum = sha(target.read_bytes())
    (output / 'SHA256SUMS.txt').write_bytes((checksum + '  ' + target.name + '\n').encode('ascii'))
    print(json.dumps({'profile': 'current', 'asset': target.name, 'sha256': checksum,
                      'bytes': target.stat().st_size, 'completeBootImage': False}))
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.output)
