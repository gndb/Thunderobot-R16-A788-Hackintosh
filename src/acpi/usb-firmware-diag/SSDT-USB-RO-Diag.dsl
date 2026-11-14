// Offline diagnostic candidate only; no EC/GPIO/PD methods are called.
// Requires one exact DSDT/XHCI _DSM to XDSM rename; forwards all other UUIDs.
DefinitionBlock ("", "SSDT", 2, "R16DBG", "USBRONLY", 0x00000001)
{
    External (\_SB.PC00.XHCI, DeviceObj)
    External (\_SB.PC00.XHCI.XDSM, MethodObj)
    External (\_SB.PC00.XHCI.PDPG, PowerResObj)
    External (\PPOE, FieldUnitObj)
    External (\UCMS, FieldUnitObj)
    External (\PSG1, FieldUnitObj)
    External (\PSG2, FieldUnitObj)
    External (\POVP, FieldUnitObj)
    External (\XDCE, FieldUnitObj)
    External (\DTFS, UnknownObj)
    Scope (\_SB.PC00.XHCI)
    {
        Method (_DSM, 4, Serialized)
        {
            If ((Arg0 == ToUUID ("a0b5b7c6-1318-441c-b0c9-fe695eaf949b")) && (Arg1 == One))
            {
                If (Arg2 == Zero) { Return (Buffer (One) { 0x03 }) }
                If (Arg2 == One)
                {
                    Local0 = Package () {
                        "r16-usb-ppoe", Buffer (8) { 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff },
                        "r16-usb-ucms", Buffer (8) { 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff },
                        "r16-usb-psg1", Buffer (8) { 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff },
                        "r16-usb-psg2", Buffer (8) { 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff },
                        "r16-usb-povp", Buffer (8) { 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff },
                        "r16-usb-xdce", Buffer (8) { 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff },
                        "r16-usb-dtfs", Buffer (8) { 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff },
                        "r16-usb-has-pdpg", Zero,
                        "r16-usb-diag-version", One
                    }
                    If (CondRefOf (\PPOE)) { Local0 [1] = ToBuffer (\PPOE) }
                    If (CondRefOf (\UCMS)) { Local0 [3] = ToBuffer (\UCMS) }
                    If (CondRefOf (\PSG1)) { Local0 [5] = ToBuffer (\PSG1) }
                    If (CondRefOf (\PSG2)) { Local0 [7] = ToBuffer (\PSG2) }
                    If (CondRefOf (\POVP)) { Local0 [9] = ToBuffer (\POVP) }
                    If (CondRefOf (\XDCE)) { Local0 [11] = ToBuffer (\XDCE) }
                    If (CondRefOf (\DTFS)) { Local0 [13] = ToBuffer (\DTFS) }
                    If (CondRefOf (\_SB.PC00.XHCI.PDPG)) { Local0 [15] = One }
                    Return (Local0)
                }
                Return (Buffer (One) { 0x00 })
            }
            Return (XDSM (Arg0, Arg1, Arg2, Arg3))
        }
    }
}
