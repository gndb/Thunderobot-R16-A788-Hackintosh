"""Synthetic offline fixtures only; no actual EFI or hardware is read."""
from pathlib import Path
import hashlib
import json
import stat
import sys
import tempfile
import unittest
import zipfile

sys.dont_write_bytecode = True
import assemble_efi as target


class AssembleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / 'repository'
        self.root.mkdir()
        self.output = self.base / 'assembled-EFI'
        self.payloads = {
            'OC/config.plist': b'owned-public-template',
            'BOOT/BOOTx64.efi': b'owned-boot-fixture',
            'OC/Kexts/Fixture.kext/Contents/MacOS/Fixture': b'owned-driver-fixture',
        }
        for name in ('OC/config.plist', 'BOOT/BOOTx64.efi'):
            p = self.root / 'EFI' / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(self.payloads[name])
        self.records = {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                        for name, data in self.payloads.items()}
        self.save_manifest()

    def save_manifest(self):
        p = self.root / 'metadata/assembly-manifest.json'
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps({'schema': 1, 'profile': 'current', 'files': self.records}), encoding='utf-8')

    def source_directory(self, data=None):
        p = self.base / 'source'
        p.mkdir()
        payload = self.payloads['OC/Kexts/Fixture.kext/Contents/MacOS/Fixture'] if data is None else data
        (p / 'arbitrary-original-filename').write_bytes(payload)
        return p

    def assert_complete(self):
        names = {p.relative_to(self.output).as_posix() for p in self.output.rglob('*') if p.is_file()}
        self.assertEqual(names, set(self.payloads))
        for name, data in self.payloads.items():
            self.assertEqual((self.output / name).read_bytes(), data)

    def test_nested_zip_matches_content_not_filename(self):
        source = self.base / 'source.zip'
        with zipfile.ZipFile(source, 'w') as archive:
            archive.writestr('official-release/renamed-binary', self.payloads['OC/Kexts/Fixture.kext/Contents/MacOS/Fixture'])
            archive.writestr('official-release/config.plist', b'private-template-must-not-be-selected')
        result = target.assemble(self.root, [source], self.output)
        self.assertEqual(result['files'], 3)
        self.assertFalse(result['bootTested'])
        self.assert_complete()

    def test_directory_matches_content_and_keeps_public_config(self):
        source = self.source_directory()
        (source / 'config.plist').write_bytes(b'private-config')
        target.assemble(self.root, [source], self.output)
        self.assert_complete()

    def test_missing_has_no_output(self):
        with self.assertRaises(target.AssemblyError) as caught:
            target.assemble(self.root, [], self.output)
        self.assertEqual(caught.exception.missing, ['OC/Kexts/Fixture.kext/Contents/MacOS/Fixture'])
        self.assertFalse(self.output.exists())

    def test_wrong_hash_has_no_output(self):
        wrong = b'x' * len(self.payloads['OC/Kexts/Fixture.kext/Contents/MacOS/Fixture'])
        with self.assertRaises(target.AssemblyError):
            target.assemble(self.root, [self.source_directory(wrong)], self.output)
        self.assertFalse(self.output.exists())

    def test_manifest_traversal_rejected(self):
        self.records['../outside'] = {'bytes': 1, 'sha256': hashlib.sha256(b'x').hexdigest()}
        self.save_manifest()
        with self.assertRaisesRegex(target.AssemblyError, 'Unsafe manifest path'):
            target.assemble(self.root, [], self.output)
        self.assertFalse(self.output.exists())
        self.assertFalse((self.base / 'outside').exists())

    def test_manifest_case_collision_rejected(self):
        self.records['oc/CONFIG.plist'] = self.records['OC/config.plist']
        self.save_manifest()
        with self.assertRaisesRegex(target.AssemblyError, 'Case-colliding'):
            target.assemble(self.root, [], self.output)

    def test_existing_output_is_preserved(self):
        self.output.mkdir()
        marker = self.output / 'existing-user-file'
        marker.write_bytes(b'keep')
        with self.assertRaisesRegex(target.AssemblyError, 'already exists'):
            target.assemble(self.root, [], self.output)
        self.assertEqual(marker.read_bytes(), b'keep')

    def test_output_inside_repository_rejected(self):
        with self.assertRaisesRegex(target.AssemblyError, 'outside the repository'):
            target.assemble(self.root, [], self.root / 'assembled')
        self.assertFalse((self.root / 'assembled').exists())

    def test_source_output_overlap_rejected(self):
        source = self.source_directory()
        with self.assertRaisesRegex(target.AssemblyError, 'overlap'):
            target.assemble(self.root, [source], source / 'new-output')
        self.assertFalse((source / 'new-output').exists())

    def test_zip_traversal_rejected_without_extraction(self):
        source = self.base / 'unsafe.zip'
        with zipfile.ZipFile(source, 'w') as archive:
            archive.writestr('../../outside', b'x')
        with self.assertRaisesRegex(target.AssemblyError, 'Unsafe ZIP'):
            target.assemble(self.root, [source], self.output)
        self.assertFalse(self.output.exists())
        self.assertFalse((self.base / 'outside').exists())

    def test_zip_symlink_rejected(self):
        source = self.base / 'symlink.zip'
        entry = zipfile.ZipInfo('release/link')
        entry.create_system = 3
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(source, 'w') as archive:
            archive.writestr(entry, 'elsewhere')
        with self.assertRaisesRegex(target.AssemblyError, 'link or special'):
            target.assemble(self.root, [source], self.output)
        self.assertFalse(self.output.exists())

    def test_directory_symlink_rejected(self):
        source = self.source_directory()
        try:
            (source / 'link').symlink_to(source / 'arbitrary-original-filename')
        except OSError:
            self.skipTest('This host does not grant symbolic-link creation')
        with self.assertRaisesRegex(target.AssemblyError, 'nonregular'):
            target.assemble(self.root, [source], self.output)
        self.assertFalse(self.output.exists())

    def test_wrong_public_config_rejected(self):
        (self.root / 'EFI/OC/config.plist').write_bytes(b'changed-private-config')
        with self.assertRaises(target.AssemblyError):
            target.assemble(self.root, [self.source_directory()], self.output)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
