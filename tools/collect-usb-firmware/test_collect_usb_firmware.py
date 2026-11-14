#!/usr/bin/env python3
"""Offline contract/privacy checks; optional fixture stays outside the repository."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch

import collect_usb_firmware as collector
import export_summary as exporter


def fixture():
    return [{'IORegistryEntryName': 'XHCI@14', 'IOObjectClass': 'IOPCIDevice',
             'IORegistryEntryID': 99, 'vendor-id': bytes.fromhex('86800000'),
             'device-id': bytes.fromhex('607a0000'),
             'r16-usb-ppoe': bytes(8), 'r16-usb-ucms': b'\xff' * 8,
             'r16-usb-psg1': (258).to_bytes(8, 'little'),
             'IORegistryEntryChildren': [
                 {'IORegistryEntryName': 'HS02@2', 'IOObjectClass': 'AppleUSB20XHCIPort',
                  'IORegistryEntryID': 100, 'port-statistics': {'kPortStatConnectCount': 0},
                  'IORegistryEntryChildren': [{'USB Serial Number': 'PRIVATE-SERIAL'}]},
                 {'IORegistryEntryName': 'SS02@2', 'IOObjectClass': 'AppleUSB30XHCIPort',
                  'IORegistryEntryID': 101, 'port-statistics': {'kPortStatConnectCount': 4,
                  'kPortStatEnumerationFailureCount': 1, 'kPortStatOverCurrentCount': 0}},
                 {'IORegistryEntryName': 'HS03@3', 'IOObjectClass': 'AppleUSB20XHCIPort'},
                 {'IORegistryEntryName': 'HS02@wrong', 'IOObjectClass': 'WrongClass'}]}]


class Contracts(unittest.TestCase):
    def test_unavailable_zero_little_endian_and_ff_are_distinct(self):
        self.assertEqual(collector.field({}, 'ppoe'),
                         {'available': False, 'reason': 'property-not-published', 'value': None})
        zero = collector.field({'r16-usb-ppoe': bytes(8)}, 'ppoe')
        self.assertTrue(zero['available']); self.assertEqual(zero['value'], 0)
        ff = collector.field({'r16-usb-ppoe': b'\xff' * 8}, 'ppoe')
        self.assertFalse(ff['available']); self.assertIsNone(ff['value'])
        self.assertEqual(ff['reason'], 'field-not-present-sentinel')
        self.assertEqual(collector.field({'r16-usb-ppoe': b'\x02\x01'}, 'ppoe')['value'], 258)
        # Only the actual eight-byte sentinel is special.
        self.assertEqual(collector.field({'r16-usb-ppoe': b'\xff' * 4}, 'ppoe')['value'], 0xffffffff)

    def test_unexpected_types_never_become_zero(self):
        for value in ['0', {}, [], b'', bytes(9), None]:
            result = collector.field({'r16-usb-ppoe': value}, 'ppoe')
            self.assertFalse(result['available']); self.assertIsNone(result['value'])
            self.assertEqual(result['reason'], 'unexpected-property-type')

    def test_port_selection_counters_children_and_deduplication(self):
        tree = fixture()
        result = collector.summarize([('fixture', tree)], [('a', tree), ('b', tree)], [])
        self.assertEqual(len(result['pciNodes']), 1)
        ports = {p['name']: p for p in result['targetPorts']}
        self.assertEqual(set(ports), {'HS02', 'SS02'})
        self.assertEqual(ports['HS02']['counters']['kPortStatConnectCount'], 0)
        self.assertIsNone(ports['HS02']['counters']['kPortStatEnumerationFailureCount'])
        self.assertEqual(ports['HS02']['directChildCount'], 1)
        self.assertIsNone(ports['SS02']['directChildCount'])
        self.assertEqual(ports['SS02']['counters']['kPortStatEnumerationFailureCount'], 1)
        self.assertFalse(result['USBRepaired']); self.assertFalse(result['PDContractVerified'])

    def test_controller_filter_retains_missing_properties(self):
        tree = [{'vendor-id': 0x8086, 'device-id': 0x7a60},
                {'vendor-id': 1, 'device-id': 2},
                {'IORegistryEntryName': 'other', 'r16-usb-ppoe': 1}]
        result = collector.summarize([('fixture', tree)], [], [])
        self.assertEqual(len(result['pciNodes']), 2)
        absent = result['pciNodes'][0]
        self.assertFalse(absent['diagnosticPropertiesPresent'])
        for value in absent['fields'].values():
            self.assertFalse(value['available']); self.assertIsNone(value['value'])

    def test_parse_failure_is_explicit(self):
        errors = []
        self.assertEqual(collector.parse(b'not a plist', 'fixture', errors), [])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['query'], 'fixture')

    def test_export_has_no_uuid_path_serial_registry_id_or_raw_children(self):
        value = collector.summarize([('fixture', fixture())], [('fixture', fixture())], [])
        secret = '00000000-DEAD-BEEF-CAFE-111111111111'
        value.update({'bootUUID': secret, 'serial': 'PRIVATE-SERIAL',
                      'registryPath': '/private/home/person/registry'})
        value['errors'] = [{'error': secret, 'path': '/private/home/person'}]
        value['pciNodes'][0].update({'name': secret, 'registryPath': secret, 'source': secret})
        value['pciNodes'][0]['fields']['dtfs'] = {'available': False, 'value': None, 'reason': secret, 'raw': secret}
        value['targetPorts'][0]['rawChildren'] = [{'serial': secret}]
        value['targetPorts'][0]['counters']['unexpected'] = secret
        safe = exporter.export_summary(value)
        encoded = json.dumps(safe)
        for forbidden in [secret, 'PRIVATE-SERIAL', '/private/', 'bootUUID', 'registryID', 'registryPath', 'rawChildren', '"raw"']:
            self.assertNotIn(forbidden, encoded)
        fields = safe['pciNodes'][0]['fields']
        self.assertTrue(fields['ppoe']['available']); self.assertEqual(fields['ppoe']['value'], 0)
        self.assertFalse(fields['ucms']['available']); self.assertIsNone(fields['ucms']['value'])
        self.assertEqual(fields['dtfs']['reason'], 'unexpected-property-type')
        self.assertEqual(safe['queryErrorCount'], 1)
        self.assertFalse(safe['USBRepaired'])

    def test_export_rejects_text_disguised_as_counters(self):
        result = exporter.export_summary({'pciNodes': [], 'targetPorts': [
            {'name': 'HS02', 'counters': {'kPortStatConnectCount': 'secret/path'}, 'directChildCount': -1},
            {'name': 'secret', 'counters': {}}]})
        self.assertEqual(len(result['targetPorts']), 1)
        self.assertIsNone(result['targetPorts'][0]['counters']['kPortStatConnectCount'])
        self.assertIsNone(result['targetPorts'][0]['directChildCount'])

    def test_replay_uses_fresh_external_output_without_hardware_commands(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'input.plist'
            source.write_bytes(plistlib.dumps(fixture()))
            out = root / 'new-output'
            with patch.object(collector.subprocess, 'run', side_effect=AssertionError('hardware query during replay')):
                result = collector.run(argparse.Namespace(replay=source, output=out))
            self.assertTrue((out / 'REPORT.md').is_file())
            self.assertTrue((out / '.raw/summary.json').is_file())
            local = json.loads((out / '.raw/summary.json').read_text(encoding='utf-8'))
            self.assertEqual(local['mode'], 'offline-replay-no-hardware-query')
            self.assertEqual(result['targetPorts'], 2)
            self.assertNotIn('PRIVATE-SERIAL', (out / 'REPORT.md').read_text(encoding='utf-8'))
            self.assertEqual(plistlib.loads(source.read_bytes()), fixture())
            with self.assertRaises(FileExistsError):
                collector.create_output(out)

    def test_replay_directory_combines_pci_and_usb_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'input'; source.mkdir()
            (source / 'pci-ioreg.stdout').write_bytes(plistlib.dumps([{'vendor-id': 0x8086, 'device-id': 0x7a60}]))
            (source / 'usb-ioreg.stdout').write_bytes(plistlib.dumps(fixture()[0]['IORegistryEntryChildren']))
            out = root / 'out'
            collector.run(argparse.Namespace(replay=source, output=out))
            local = json.loads((out / '.raw/summary.json').read_text(encoding='utf-8'))
            self.assertEqual(len(local['pciNodes']), 1)
            self.assertEqual({p['name'] for p in local['targetPorts']}, {'HS02', 'SS02'})
            self.assertFalse(local['diagnosticPropertiesObserved'])

    def test_repository_output_refused(self):
        root = collector.repository_root()
        if root is None:
            self.skipTest('Source is outside a Git repository')
        out = root / 'must-not-create-raw-collector-test-output'
        with self.assertRaisesRegex(ValueError, 'outside this repository'):
            collector.create_output(out)
        self.assertFalse(out.exists())

    def test_default_destination_is_desktop_outside_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(collector.Path, 'home', return_value=Path(temporary)):
                out, raw = collector.create_output()
            self.assertEqual(out.parent, Path(temporary) / 'Desktop/R16-USB-Reports')
            self.assertEqual(raw, out / '.raw')

    def test_export_command_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'summary.json'; output = root / 'export.json'
            source.write_text(json.dumps(collector.summarize([], [], [])), encoding='utf-8')
            with patch('sys.argv', ['export_summary.py', str(source), '--output', str(output)]):
                with contextlib.redirect_stdout(io.StringIO()): exporter.main()
            saved = output.read_bytes()
            with patch('sys.argv', ['export_summary.py', str(source), '--output', str(output)]):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error: exporter.main()
            self.assertEqual(error.exception.code, 2); self.assertEqual(output.read_bytes(), saved)


def check_private_fixture(source):
    with tempfile.TemporaryDirectory() as temporary:
        out = Path(temporary) / 'fixture-replay'
        with patch.object(collector.subprocess, 'run', side_effect=AssertionError('hardware query during replay')):
            collector.run(argparse.Namespace(replay=source, output=out))
        local = json.loads((out / '.raw/summary.json').read_text(encoding='utf-8'))
        safe = exporter.export_summary(local)
        assert not local['errors'], 'Fixture must parse without errors'
        assert {p['name'] for p in safe['targetPorts']} == {'HS02', 'SS02'}, 'Expected target ports not found'
        # Retain the distinction for every field actually encountered in the snapshot.
        for node, exported in zip(local['pciNodes'], safe['pciNodes']):
            for name in collector.FIELDS:
                if not node['fields'][name]['available']:
                    assert exported['fields'][name]['value'] is None
        text = json.dumps(safe)
        for key in ['bootUUID', 'registryID', 'registryPath', 'serial', 'rawChildren']:
            assert key not in text, 'Private field escaped whitelist'
        return {'parsed': True, 'targetPorts': sorted({p['name'] for p in safe['targetPorts']}),
                'pciNodes': len(safe['pciNodes']), 'queryErrors': len(local['errors']),
                'diagnosticPropertiesObserved': safe['diagnosticPropertiesObserved']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-fixture', type=Path)
    args, remaining = parser.parse_known_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    if not result.wasSuccessful():
        raise SystemExit(1)
    if args.private_fixture:
        print('Private fixture result: ' + json.dumps(check_private_fixture(args.private_fixture), sort_keys=True))
