# Source and verification

This standalone candidate builder is parameterized from the R16 installation
mechanism, not copied from the complete private deployment controller.
It does not include an activation or rollback operation.

Upstream comparison: WhateverXe Graphics commit
`61c7cddda38d6a5d0057a01f402aab6efb612e13`, `tools/auxkc.sh`, which
currently passes local `/Library/Extensions/*.kext` bundles only.
The observed R16 auxiliary collection additionally had a member under
`/Library/Apple/System/Library/Extensions`.

The current 32 test results are freshly run portable, isolated source tests
with a mocked command runner. The historical installation helper had 14
modeled cases and a separate actual cache rebuild. Those facts do not prove
this newly parameterized tool has been hardware-tested. Live rollback was
not exercised, and this tool deliberately cannot activate or roll back.

Independent review found that an earlier parser ignored non-tabular nonempty
lines in the auxiliary section. That could hide an unrecognized existing member.
The parser now accepts only the exact `Extension Information:` header, blank
lines and validated three-field rows (plus an optional trailing tab). Changed
formats, extra columns, duplicate auxiliary sections and invalid paths fail
closed. Fresh parser and candidate-output regressions cover this correction.
