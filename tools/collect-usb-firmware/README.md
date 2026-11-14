# R16 USB firmware collector

This **read-only** Python 3 tool reads already-published PCI properties and HS02/SS02 counters. It does not evaluate ACPI methods, reset ports, change power settings, write EFI, or repair USB/Type-C Power Delivery. USB/PD on this R16 remains unresolved.

On macOS, run without `sudo`:

```sh
python3 collect_usb_firmware.py
```

Output is a new `~/Desktop/R16-USB-Reports/<UTC-stamp>/` directory, outside the repository. `REPORT.md` shows the limited observations. Hidden `.raw/` contains the IORegistry records, boot session UUID, query receipts and local summary. Raw hardware records can contain private identifiers: **do not upload `.raw/`, the whole collection directory, or a raw replay fixture**. Hidden is presentation, not encryption.

Choose another new output directory with `--output /path/to/new-directory`. Existing directories are refused; output inside this Git repository is refused. Both collection and replay have the same output policy.

Offline replay works on Windows, Linux and macOS and runs no hardware commands:

```sh
python3 collect_usb_firmware.py --replay /path/to/saved-ioreg.plist --output /path/to/new-directory
```

Input may also be a collection directory or its `.raw/` folder. Known PCI/USB `.stdout` and `.plist` records are parsed together. The output is always a fresh directory, never the input directory.

To share observations, export the small **whitelist** JSON and review it:

```sh
python3 export_summary.py /path/to/collection --output /path/to/new-public-summary.json
```

The exporter retains only PCI vendor/device numbers, the fixed diagnostic field names, HS02/SS02 numeric counters and child counts. It omits boot UUID, registry paths and IDs, node names, serials, raw properties/children, arbitrary error text and source paths. It refuses to overwrite the output file. This is a data-minimizing export, not permission to publish someone else's report.

Missing fields and counters remain unavailable/null, **never zero**. An eight-byte all-FF diagnostic value means unavailable. A real numeric zero remains available. PSG1/PSG2 are firmware parameters, not measured GPIO levels; the fields are enumeration snapshots, not live VBUS or negotiated PD measurements. `USBRepaired`, `VBUSMeasured` and `PDContractVerified` remain false.

Run the synthetic contract/privacy tests with `python3 test_collect_usb_firmware.py`. A private saved snapshot can optionally be replay-tested with `--private-fixture /path/to/usb-ioreg.stdout`; it is never copied into this repository. Tests establish offline parsing, output policy and export behavior, not a new macOS hardware collection or a USB fix. See [TEST_RESULTS.md](TEST_RESULTS.md) for the checked scope.

This tool is derived from the R16 local collector with the same field and target-port semantics. It has no dependency on a share volume layout. MIT license; Python standard library only.
