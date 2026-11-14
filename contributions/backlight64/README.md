# R16 native-backlight 64-bit arithmetic: research contribution

This directory provides a bounded CPU regression for the arithmetic window in
the deployed R16 WhateverXe patch. It is **not an independent patch ready for
upstream main**, and it does not install anything.

## Contract and evidence

For an unsigned 32-bit PWM period and a brightness request in `0..65535`, the
required duty is `floor(period * raw / 65535)`. The native sequence multiplies in
32 bits before division, so a period of 96000 fails the full-brightness endpoint.
The R16 sequence uses the 64-bit product and exact unsigned division. Its
arithmetic window is 23 bytes; the native function context is 105 bytes and must
match exactly at the pinned offset, with exactly one arithmetic signature.

`kern_r16_backlight64.hpp` is copied byte-for-byte from the R16 0.8.2 source
reconstructed from official tag `0.8.2` (`4512191b...`) plus the published R16
production patch. Do not alter the header and continue to claim that identity.
Keep the upstream BSD-3-Clause license in this directory.

## Run

On an x86_64 Linux host with Clang:

```sh
clang++ -std=c++17 -O2 -Wall -Wextra backlight64_contract.cpp -o /tmp/backlight64-contract
/tmp/backlight64-contract
```

The test executes the actual old and replacement arithmetic bytes through an
owned, generated SysV ABI fixture. It checks all 65536 brightness inputs for
nine independent PWM periods, including `UINT32_MAX`, against an independent
quotient/remainder oracle. It also checks monotonicity, bounds, the old overflow
counterexample, a duplicate signature, a short mapping, a wrong function offset,
and every altered byte of the expected function context.

This does **not** execute the Apple driver, MMIO, the native call graph, a
macOS kernel patcher, a physical display, or sleep/wake. It does not prove that
upstream main reaches this arithmetic path. Historical large test counts whose
raw logs are missing are not reused as results of this test.

## Why this is not submitted as a standalone upstream fix

The upstream main inspected at `2bad71718c6b4f9887e2a504a19a24c3593ea1db`
has `wrapADLSPanelBacklight` return `NotReady` when qualified PWM capture fails.
The deployed R16 native arithmetic repair runs through an additional native
donor-backlight fallback. That fallback and its R16 R5/R6 readiness state are
part of the larger production patch, not current upstream main.

Adding just the 64-bit byte replacement to main would not establish a working
production entry-to-consumer path. Adding the unrelated R16 initialization and
fallback stack would no longer be a small arithmetic PR. The next upstream
step is to agree on and qualify the native fallback contract (see upstream
issue [31](https://github.com/b00t0x/WhateverXe/issues/31)), then attach this
arithmetic fix and its tests to that real consumer.

The fallback research in that issue is by `rodgod-rr`; this contribution does
not claim that mechanism as new work. Existing firmware-wiring/deferred-
activation work is also not claimed as part of the arithmetic fix.

Repository AGENTS.md requests a `codex/next-release` base, but the upstream
branch listing at review time exposed only `main`. The isolated checkout was
based on main for analysis; no production source there was changed, committed,
or pushed, and no PR was opened by this preparation task.
