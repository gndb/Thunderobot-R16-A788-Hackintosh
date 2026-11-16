#!/usr/bin/env python3
"""Read already-published R16 PCI firmware properties and USB counters once.

No sudo, ACPI method evaluation, port reset, EFI write or power-setting change.
Live collection requires macOS; --replay parses a saved plist on any platform.
Raw local evidence is private. Export only export_summary.py's whitelist output.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys

from export_summary import export_summary, TARGET_PORTS, OTHER_PORTS

FIELDS = ('ppoe', 'ucms', 'psg1', 'psg2', 'povp', 'xdce', 'dtfs', 'has-pdpg', 'diag-version')
COUNTERS = ('kPortStatConnectCount', 'kPortStatEnumerationFailureCount', 'kPortStatOverCurrentCount')
MAX_RAW = 32 * 1024 * 1024


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def walk(value):
    if isinstance(value, list):
        for item in value:
            yield from walk(item)
    elif isinstance(value, dict):
        yield value
        yield from walk(value.get('IORegistryEntryChildren', []))


def wire(value):
    if isinstance(value, bytes):
        return {'hex': value.hex(), 'bytes': len(value)}
    if isinstance(value, dict):
        return {str(k): wire(v) for k, v in value.items()}
    if isinstance(value, list):
        return [wire(v) for v in value]
    return value


def integer(value):
    if isinstance(value, int):
        return value
    if isinstance(value, bytes) and 0 < len(value) <= 8:
        return int.from_bytes(value, 'little')
    return None


def field(node, suffix):
    key = 'r16-usb-' + suffix
    if key not in node:
        return {'available': False, 'reason': 'property-not-published', 'value': None}
    raw = node[key]
    if isinstance(raw, bytes) and raw == b'\xff' * 8:
        return {'available': False, 'reason': 'field-not-present-sentinel', 'value': None, 'raw': wire(raw)}
    number = integer(raw)
    if number is None:
        return {'available': False, 'reason': 'unexpected-property-type', 'value': None, 'raw': wire(raw)}
    return {'available': True, 'value': number, 'raw': wire(raw)}


def parse(raw, label, errors):
    try:
        return plistlib.loads(raw)
    except (ValueError, TypeError, plistlib.InvalidFileException) as exc:
        errors.append({'query': label, 'parseError': str(exc)})
        return []


def summarize(pci_sources, port_sources, errors):
    pci, seen = [], set()
    for label, value in pci_sources:
        for node in walk(value):
            has_properties = any('r16-usb-' + key in node for key in FIELDS)
            vendor, device = integer(node.get('vendor-id')), integer(node.get('device-id'))
            if not has_properties and (vendor, device) != (0x8086, 0x7a60):
                continue
            ident = (label, node.get('IORegistryEntryID'), node.get('IORegistryEntryName'))
            if ident in seen:
                continue
            seen.add(ident)
            pci.append({'source': label, 'name': node.get('IORegistryEntryName'),
                        'class': node.get('IOObjectClass'), 'registryID': node.get('IORegistryEntryID'),
                        'vendorID': vendor, 'deviceID': device, 'diagnosticPropertiesPresent': has_properties,
                        'fields': {key: field(node, key) for key in FIELDS}})
    ports, seen = [], set()
    for label, value in port_sources:
        for node in walk(value):
            name = str(node.get('IORegistryEntryName', '')).split('@')[0]
            klass = str(node.get('IOObjectClass', ''))
            if name not in TARGET_PORTS + OTHER_PORTS or not ('XHCIPort' in klass or 'USBHostPort' in klass):
                continue
            ident = (node.get('IORegistryEntryID'), name, klass, node.get('IORegistryEntryLocation'))
            if ident in seen:
                continue
            seen.add(ident)
            statistics = node.get('port-statistics', {})
            if not isinstance(statistics, dict):
                statistics = {}
            children = node.get('IORegistryEntryChildren')
            ports.append({'source': label, 'name': name, 'class': klass,
                          'registryID': node.get('IORegistryEntryID'),
                          'counters': {key: statistics.get(key) for key in COUNTERS},
                          'properties': wire({key: node[key] for key in
                              ('UsbConnector', 'usb-port-number', 'usb-port-type', 'port', 'port-status', 'IOPowerManagement')
                              if key in node}),
                          'directChildCount': len(children) if isinstance(children, list) else None})
    return {'capturedUTC': utc(), 'pciNodes': pci, 'targetPortNames': list(TARGET_PORTS),
            'targetPorts': [p for p in ports if p['name'] in TARGET_PORTS],
            'otherObservedPorts': [p for p in ports if p['name'] in OTHER_PORTS],
            'diagnosticPropertiesObserved': any(x['diagnosticPropertiesPresent'] for x in pci),
            'errors': errors, 'USBRepaired': False, 'VBUSMeasured': False, 'PDContractVerified': False,
            'firmwareFieldsAreEnumerationSnapshot': True,
            'diagnosticInterpretation': 'Missing properties and FF*8 sentinel are unavailable, never substituted with zero. PSG1/PSG2 are firmware parameters, not measured GPIO levels.'}


def hide_raw(directory):
    warnings = []
    for p in [directory] + list(directory.iterdir()):
        try:
            if sys.platform == 'darwin':
                os.chflags(str(p), p.stat().st_flags | 0x8000)
            elif os.name == 'nt':
                import ctypes
                api = ctypes.windll.kernel32
                api.GetFileAttributesW.restype = ctypes.c_uint32
                attrs = api.GetFileAttributesW(str(p))
                if attrs == 0xffffffff or not api.SetFileAttributesW(str(p), attrs | 2):
                    raise OSError('Could not mark raw evidence Hidden')
        except OSError:
            warnings.append('raw-hidden-attribute-unavailable')
    return warnings


def query(out, label, argv, errors, manifest):
    try:
        run = subprocess.run(argv, capture_output=True, timeout=20)
        raw = run.stdout
        if len(raw) > MAX_RAW or len(run.stderr) > MAX_RAW:
            raise ValueError('Bounded query exceeded 32 MiB')
        (out / (label + '.stdout')).write_bytes(raw)
        (out / (label + '.stderr')).write_bytes(run.stderr)
        manifest[label] = {'argv': argv, 'exitCode': run.returncode, 'bytes': len(raw),
                           'sha256': hashlib.sha256(raw).hexdigest()}
        if run.returncode != 0:
            errors.append({'query': label, 'exitCode': run.returncode})
        return raw
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        errors.append({'query': label, 'error': str(exc)})
        manifest[label] = {'argv': argv, 'error': str(exc)}
        return b''


def repository_root():
    for directory in Path(__file__).resolve().parents:
        if (directory / '.git').exists():
            return directory
    return None


def create_output(requested=None):
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = (requested or Path.home() / 'Desktop' / 'R16-USB-Reports' / stamp).expanduser().resolve()
    root = repository_root()
    if root is not None and (out == root or root in out.parents):
        raise ValueError('Output must be outside this repository; raw hardware records must not be committed')
    out.mkdir(parents=True, exist_ok=False)
    raw = out / '.raw'
    raw.mkdir()
    return out, raw


def replay_inputs(source):
    source = source.expanduser().resolve()
    if source.is_file():
        return [('replay', source)]
    if not source.is_dir():
        raise ValueError('Replay input must be an existing plist or collection directory')
    if (source / '.raw').is_dir():
        source = source / '.raw'
    inputs = []
    for stem in ('pci-ioreg', 'pci-device-tree', 'usb-ioreg', 'HS04', 'SS02', 'HS02', 'replay-source'):
        p = next((source / (stem + suffix) for suffix in ('.stdout', '.plist')
                  if (source / (stem + suffix)).is_file()), None)
        if p is not None:
            inputs.append((stem, p))
    if not inputs:
        inputs = [('replay', p) for p in sorted(source.glob('*.plist'))]
    if not inputs:
        raise ValueError('No supported IORegistry plist found in replay directory')
    return inputs


def collect_replay(source, raw_out, errors, manifest):
    parsed = []
    for index, (label, path) in enumerate(replay_inputs(source)):
        if path.stat().st_size > MAX_RAW:
            raise ValueError('Replay input exceeds 32 MiB')
        raw = path.read_bytes()
        if len(raw) > MAX_RAW:
            raise ValueError('Replay input exceeds 32 MiB')
        (raw_out / ('replay-' + str(index) + '.plist')).write_bytes(raw)
        manifest[label] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        parsed.append((label, parse(raw, label, errors)))
    summary = summarize(parsed, parsed, errors)
    summary['mode'] = 'offline-replay-no-hardware-query'
    return summary


def report(summary):
    safe = export_summary(summary)
    rows = ['# R16 USB firmware observation', '',
            'Read-only observation. USB and Type-C/PD are **not repaired or verified** by this tool.', '',
            'Firmware fields are PCI enumeration snapshots, not live VBUS, GPIO-level or PD-contract measurements.', '',
            '## PCI firmware fields', '']
    if not safe['pciNodes']:
        rows.append('No target PCI node was observed. Missing properties do not mean zero.')
    for index, pci in enumerate(safe['pciNodes']):
        rows.extend(['### Target PCI node ' + str(index + 1), '', '| Field | Observation |', '|---|---|'])
        for key in FIELDS:
            value = pci['fields'][key]
            text = str(value['value']) + ' (' + hex(value['value']) + ')' if value['available'] else 'Unavailable: ' + value['reason']
            rows.append('| ' + key + ' | ' + text + ' |')
        rows.append('')
    rows.extend(['## Rear Type-C: HS04 / SS02', '', '```json', json.dumps(safe['targetPorts'], indent=2), '```', '',
                 'Only HS04 and SS02 belong to the current rear Type-C target pair.', '',
                 '## Other saved observations (not the rear Type-C pair)', '', '```json',
                 json.dumps(safe['otherObservedPorts'], indent=2), '```', '',
                 'Missing counters remain null. Eight FF bytes mean an unavailable firmware field, not zero.', '',
                 'Private raw evidence and local summary are in `.raw/`. Do not upload that directory.',
                 'For sharing, run `export_summary.py` and review its small whitelist JSON.', ''])
    return '\n'.join(rows)


def run(args):
    if not args.replay and sys.platform != 'darwin':
        raise ValueError('Live collection runs on macOS only; use --replay for offline validation')
    # Check that input exists before making a fresh output directory.
    if args.replay:
        replay_inputs(args.replay)
    out, raw_out = create_output(args.output)
    errors, manifest = [], {}
    if args.replay:
        summary = collect_replay(args.replay, raw_out, errors, manifest)
    else:
        pci = query(raw_out, 'pci-ioreg', ['/usr/sbin/ioreg', '-a', '-l', '-r', '-c', 'IOPCIDevice', '-d', '1'], errors, manifest)
        tree = query(raw_out, 'pci-device-tree', ['/usr/sbin/ioreg', '-a', '-l', '-r', '-p', 'IODeviceTree', '-n', 'XHCI', '-d', '1'], errors, manifest)
        hs = query(raw_out, 'HS04', ['/usr/sbin/ioreg', '-a', '-l', '-r', '-n', 'HS04', '-d', '2'], errors, manifest)
        ss = query(raw_out, 'SS02', ['/usr/sbin/ioreg', '-a', '-l', '-r', '-n', 'SS02', '-d', '2'], errors, manifest)
        boot = query(raw_out, 'boot-id', ['/usr/sbin/sysctl', '-n', 'kern.bootsessionuuid'], errors, manifest)
        summary = summarize([('PCI-IOService', parse(pci, 'pci-ioreg', errors)),
                             ('PCI-IODeviceTree', parse(tree, 'pci-device-tree', errors))],
                            [('HS04', parse(hs, 'HS04', errors)), ('SS02', parse(ss, 'SS02', errors))], errors)
        summary['mode'] = 'macOS-read-only-state-collection'
        summary['bootUUID'] = boot.decode('utf-8', 'replace').strip() or None
    (raw_out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (raw_out / 'queries.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'REPORT.md').write_text(report(summary), encoding='utf-8')
    warnings = hide_raw(raw_out)
    return {'report': str(out / 'REPORT.md'), 'raw': str(raw_out),
            'diagnosticPropertiesObserved': summary['diagnosticPropertiesObserved'],
            'pciNodes': len(summary['pciNodes']), 'targetPorts': len(summary['targetPorts']),
            'USBRepaired': False, 'visibilityWarnings': warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', type=Path, help='Saved IORegistry plist or collection directory; no hardware query')
    parser.add_argument('--output', type=Path, help='New output directory outside the repository (must not exist)')
    args = parser.parse_args()
    try:
        result = run(args)
    except (OSError, ValueError) as exc:
        parser.exit(2, 'Collection failed: ' + str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
