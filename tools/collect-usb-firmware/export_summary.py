#!/usr/bin/env python3
"""Export only bounded numeric USB diagnostic fields; never raw registry data."""
import argparse
import json
from pathlib import Path

FIELDS = ('ppoe', 'ucms', 'psg1', 'psg2', 'povp', 'xdce', 'dtfs', 'has-pdpg', 'diag-version')
COUNTERS = ('kPortStatConnectCount', 'kPortStatEnumerationFailureCount', 'kPortStatOverCurrentCount')
REASONS = {'property-not-published', 'field-not-present-sentinel', 'unexpected-property-type'}


def number(value):
    return value if type(value) is int and 0 <= value <= 0xffffffffffffffff else None


def export_field(value):
    if not isinstance(value, dict):
        value = {}
    n = number(value.get('value'))
    if value.get('available') is True and n is not None:
        return {'available': True, 'value': n}
    reason = value.get('reason')
    return {'available': False, 'value': None,
            'reason': reason if reason in REASONS else 'unexpected-property-type'}


def export_summary(value):
    if not isinstance(value, dict):
        raise ValueError('Expected a summary object')
    pci = []
    for node in value.get('pciNodes', []):
        if not isinstance(node, dict):
            continue
        fields = node.get('fields', {})
        if not isinstance(fields, dict):
            fields = {}
        pci.append({'vendorID': number(node.get('vendorID')), 'deviceID': number(node.get('deviceID')),
                    'diagnosticPropertiesPresent': node.get('diagnosticPropertiesPresent') is True,
                    'fields': {k: export_field(fields.get(k)) for k in FIELDS}})
    ports = []
    for port in value.get('targetPorts', []):
        if not isinstance(port, dict) or port.get('name') not in ('HS02', 'SS02'):
            continue
        counters = port.get('counters', {})
        if not isinstance(counters, dict):
            counters = {}
        ports.append({'name': port['name'], 'counters': {k: number(counters.get(k)) for k in COUNTERS},
                      'directChildCount': number(port.get('directChildCount'))})
    errors = value.get('errors')
    return {'schema': 1, 'scope': 'R16-USB-whitelist-summary',
            'mode': 'offline-replay' if value.get('mode') == 'offline-replay-no-hardware-query' else 'collection',
            'pciNodes': pci, 'targetPorts': ports,
            'diagnosticPropertiesObserved': any(n['diagnosticPropertiesPresent'] for n in pci),
            'queryErrorCount': len(errors) if isinstance(errors, list) else None,
            'USBRepaired': False, 'VBUSMeasured': False, 'PDContractVerified': False,
            'firmwareFieldsAreEnumerationSnapshot': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='Collection directory, .raw directory, or local summary.json')
    parser.add_argument('--output', required=True, type=Path, help='New summary JSON file; never overwrite')
    args = parser.parse_args()
    source = args.input.expanduser().resolve()
    if source.is_dir():
        source = source / ('.raw/summary.json' if (source / '.raw').is_dir() else 'summary.json')
    try:
        if source.stat().st_size > 32 * 1024 * 1024:
            raise ValueError('Summary input exceeds 32 MiB')
        safe = export_summary(json.loads(source.read_text(encoding='utf-8-sig')))
        output = args.output.expanduser().resolve()
        with output.open('x', encoding='utf-8') as f:
            f.write(json.dumps(safe, ensure_ascii=True, indent=2) + '\n')
    except (OSError, ValueError) as exc:
        parser.exit(2, 'Export failed: ' + str(exc) + '\n')
    print('Wrote whitelist summary; review it before sharing.')


if __name__ == '__main__':
    main()
