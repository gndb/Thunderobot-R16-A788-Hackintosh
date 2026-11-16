# Offline validation records

## 2026-11-16 update: corrected rear Type-C target

All **15 synthetic contract/privacy tests passed** on Windows. The current collector and schema2 export target **HS04/SS02**. A mocked live-collection test checks that the query argv names HS04 rather than HS02; subprocess execution is blocked, so this is an offline routing check, not a hardware collection.

Regression cases read an old `HS02.stdout` capture and an old schema1-style local summary. HS02 counters remain separately under `otherObservedPorts`, retain the real HS02 name, and never become HS04 or appear in the current target pair. Missing HS04 is not filled from HS02. Existing field-null/sentinel, privacy, deduplication, output-location and overwrite checks continue to pass.

No private historical fixture was rerun for this update, and no live macOS commands or new USB/PD acceptance tests were executed. The November 14 record below is preserved with its original target and scope.

## Historical November 14 run

Checked on Windows with Python 3.12. All **12 synthetic contract/privacy tests passed**. No live macOS hardware commands were run by this validation.

The tests distinguish missing diagnostic fields, true zero, little-endian byte values, the exact eight-byte FF sentinel, and unexpected types. They check HS02/SS02 class filtering and deduplication, missing counters, local parse errors, new output directories, repository output refusal, default Desktop output, multi-record replay and export overwrite refusal. Replay tests replace the subprocess runner with a failing mock, so an attempted hardware command would fail the test.

Privacy checks insert a synthetic UUID, serial, registry path/ID, raw child data and arbitrary error/reason strings. None survives the whitelist export or the human report. Numeric zero remains a value; missing counters remain null. Raw evidence is excluded from these published test files.

A separate private **15:20 saved IORegistry fixture** (4,450,232 bytes) was replayed from outside the repository. Parsing completed without errors and found HS02 and SS02. The snapshot contained no target PCI diagnostic properties; this absence was retained, with no invented zero values. Port counters explicitly present in the snapshot were retained as zero and child count remained null. The private fixture is not distributed.

For that fixture, the public parser's entire semantic summary equalled the original local collector's summary after removing only the capture timestamp. This checks preservation of the existing field/port semantics on the available recorded input. It does not establish a new USB connection, a PD charging contract, firmware property publication by the experimental SSDT, or that USB has been repaired.
