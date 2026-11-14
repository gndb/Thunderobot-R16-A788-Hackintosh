# Review an AuxKC candidate while preserving existing members

This optional tool is extracted from the R16 installation work. It generates a
reviewable plan, includes already registered bundles outside `/Library/Extensions`,
checks all reviewed input bytes again around generation, and inspects the result.
**It never replaces the live AuxiliaryKernelExtensions.kc, installs kexts, changes
EFI or performs rollback.**

The observed case was an existing auxiliary member under
`/Library/Apple/System/Library/Extensions`, which is not covered by a glob of
`/Library/Extensions/*.kext`. No Apple bundle or kernel collection is distributed.

## Use

On the target macOS, save a normal `kmutil inspect -A … -B … -S …
--show-extension-info` result. Generate a private plan with explicit inputs:

```sh
python3 auxkc_preserve.py plan --inspection before.txt --output plan.json
```

The defaults are standard macOS locations, not a machine-specific volume. Override
`--extensions`, `--boot-kc`, `--system-kc` and `--existing-aux-kc` when needed.
Review the paths and identities. `--exclude-existing-id` only acknowledges an
explicitly removed old member; it does not remove an installed bundle. Add
`--allow-missing-kdk` only for a target kmutil version that supports it.

After review, macOS can build into a **new** candidate path and log directory:

```sh
sudo python3 auxkc_preserve.py build-candidate --plan plan.json \
  --candidate /Library/KernelCollections/ReviewedCandidate.kc --logs /private/tmp/auxkc-review
```

The existing collection remains unchanged. Activating a candidate requires a
separately reviewed installation transaction and backup; this tool deliberately
does not implement that operation. Keep runtime plans/logs private or sanitize
their paths before sharing.

## Verification and limits

```sh
python3 test_auxkc_preserve.py
```

The isolated tests mock kmutil and do not run privileged commands. They verify
generation/inspection failure, missing or substring identities, interruptions,
input changes, new local bundles, duplicate/relative paths and existing output.
Inspection parsing also rejects unrecognized nonempty auxiliary lines, extra
columns, duplicate sections and malformed identities/paths; only the exact
`Extension Information:` header and blank lines are skipped.
They are distinct from the historical R16 helper's 14 modeled cases and its one
real candidate build. This newly parameterized tool has **not** been run on
macOS or used to activate a cache; real rollback has not been exercised.

Symlinked bundle inputs are rejected. Candidate publication requires hard-link
support in its parent directory; a destination appearing during generation is
never overwritten. A changed `kmutil inspect` text format fails closed instead
of silently dropping members. Hardware, code-signing, KDK and cross-OS behavior
remain the user's installation prerequisites, not results of the model tests.

The R16 original algorithm and these tools are MIT licensed; see `LICENSE`.
