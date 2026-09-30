# OAFF v0.1 draft conformance

The [fixture manifest](../fixtures/manifest.json) is the public test corpus.
The [specification](../spec/OAFF-v0.1.md) and [schema](../schema/oaff-0.1.schema.json)
remain normative; this runner tests a limited, observable subset. Passing it
does not prove semantic support, issuer identity, source availability, or
permission to adopt a Finding.

An implementation can use any language or storage system. Expose a command
that accepts one package path and prints a JSON object with `status`,
`integrity`, `diagnostics`, and `local_authority`. The existing OAFF CLI prints
a one-element JSON array; the runner accepts either shape. Use exit code 0
for valid or valid-with-limits, 1 for invalid, and 2 for usage errors. For an
invalid package, include a diagnostic code matching the manifest class.

Run the corpus from this repository:

```sh
python scripts/conformance.py -- oaff verify '{file}' --json
```

The runner substitutes `{file}` with an absolute fixture path and executes
the command directly without a shell. It imposes a 30-second timeout per
case. In CI, pin both the OAFF repository commit and the tested implementation
version. A clean-room implementation should report its version and the
language/runtime in its own CI log.

The v0.1 corpus tests eight valid and seven invalid packages. It does not yet
test network transfer, signatures, authenticated lifecycle updates,
cross-workspace adoption, or every Unicode/JCS edge case. Add focused
fixtures and update the manifest when a normative invariant is clarified.
Keep existing fixture meanings stable within a published version.
