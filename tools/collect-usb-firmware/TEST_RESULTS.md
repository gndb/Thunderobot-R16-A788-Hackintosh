# Offline validation — 2026-11-14

Checked on Windows with Python 3.12. All **12 synthetic contract/privacy tests passed**. No live macOS hardware commands were run by this validation.

The tests distinguish missing diagnostic fields, true zero, little-endian byte values, the exact eight-byte FF sentinel, and unexpected types. They check HS02/SS02 class filtering and deduplication, missing counters, local parse errors, new output directories, repository output refusal, default Desktop output, multi-record replay and export overwrite refusal. Replay tests replace the subprocess runner with a failing mock, so an attempted hardware command would fail the test.

Privacy checks insert a synthetic UUID, serial, registry path/ID, raw child data and arbitrary error/reason strings. None survives the whitelist export or the human report. Numeric zero remains a value; missing counters remain null. Raw evidence is excluded from these published test files.

A separate private **15:20 saved IORegistry fixture** (4,450,232 bytes) was replayed from outside the repository. Parsing completed without errors and found HS02 and SS02. The snapshot contained no target PCI diagnostic properties; this absence was retained, with no invented zero values. Port counters explicitly present in the snapshot were retained as zero and child count remained null. The private fixture is not distributed.

For that fixture, the public parser's entire semantic summary equalled the original local collector's summary after removing only the capture timestamp. This checks preservation of the existing field/port semantics on the available recorded input. It does not establish a new USB connection, a PD charging contract, firmware property publication by the experimental SSDT, or that USB has been repaired.
