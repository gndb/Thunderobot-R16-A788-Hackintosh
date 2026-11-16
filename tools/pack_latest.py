"""Pack the complete current EFI runtime tree, excluding inactive backups."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            result.update(block)
    return result.hexdigest()


def build(output):
    output = output.resolve()
    if output.is_relative_to(ROOT):
        raise ValueError('Output must be outside the repository.')
    sys.dont_write_bytecode = True
    from verify_package import verify
    verify(ROOT, 'current')
    manifest = json.loads((ROOT / 'metadata/efi-manifest.json').read_text(encoding='utf-8-sig'))
    meta = json.loads((ROOT / 'metadata/current.json').read_text(encoding='utf-8-sig'))
    if len(manifest) != 179 or not meta.get('identityPublishedWithOwnerConsent'):
        raise ValueError('Expected the owner-approved complete runtime EFI.')
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'R16-A788-minimal-complete-20261116.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, record in sorted(manifest.items()):
            if 'config.plist.' in name or '.kext.nullmoth-' in name:
                raise ValueError('Inactive backup in runtime manifest.')
            source = ROOT / 'EFI' / name
            if source.stat().st_size != record['bytes'] or digest(source) != record['sha256']:
                raise ValueError('Runtime file mismatch: ' + name)
            archive.write(source, 'EFI/' + name)
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != {'EFI/' + name for name in manifest}:
            raise ValueError('Archive contents differ from the runtime manifest.')
        for name, record in manifest.items():
            checksum, size = hashlib.sha256(), 0
            with archive.open('EFI/' + name) as stream:
                while block := stream.read(1024 * 1024):
                    checksum.update(block)
                    size += len(block)
            if size != record['bytes'] or checksum.hexdigest() != record['sha256']:
                raise ValueError('Archive readback mismatch: ' + name)
    checksum = digest(target)
    (output / 'SHA256SUMS.txt').write_bytes((checksum + '  ' + target.name + '\n').encode())
    print(json.dumps({'asset': target.name, 'files': len(manifest), 'bytes': target.stat().st_size,
                      'sha256': checksum, 'completeBootImage': True, 'runtimeVerified': False}))
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output)
