# R16 passive USB firmware diagnostic

This optional experiment wraps the R16 XHCI `_DSM` to expose read-only firmware state for diagnosis. It does not repair USB port routing or USB-C Power Delivery, and no post-deployment macOS property readback has yet been captured.

`patch-plan.json` scopes a single method rename to the exact DSDT length/OEM table ID and a surrounding instruction pattern. It is not a global `_DSM` rename. The fixed Apple device-properties UUID is a public protocol identifier, not the machine's SMBIOS UUID. Revision 1 functions 0/1 provide the passive diagnostic; unknown UUID/revision requests forward to original `XDSM`. The added branch makes no hardware-method calls or EC/GPIO/PD writes. Original GNVS read/lock behavior is retained.

Build with ACPICA `iasl -ve -tc SSDT-USB-RO-Diag.dsl`, then inspect the disassembly and namespace against your own firmware before using it. The checked 666-byte AML is included in the default root EFI. Earlier diagnostic profiles are retained in the fixed archive listed in docs/HISTORY.md. Compare its SHA-256 with the plan. The November 14 successful baseline is kept separate in `profiles/usable-20261114`.

These names and offsets are R16 firmware-specific. Use the collector in `tools/collect-usb-firmware` for observations; do not copy this SSDT onto another firmware merely because its USB connector looks similar.
