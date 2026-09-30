# Contributing to AFF

AFF's OAFF v0.1 wire contract is a draft. Open an issue for a concrete interoperability problem,
preferably with a minimal package or fixture that contains no secrets or
private source bytes. State which fields another implementation could not
produce or interpret, the expected behavior, and the trust boundary involved.

For a format change, submit a PR that updates the normative spec, JSON Schema,
positive or negative fixtures, manifest, verifier, conformance documentation,
and migration note together as applicable. Preserve unknown namespaced
extensions and do not turn an origin receipt into local authority. Run:

```sh
python scripts/check_fixtures.py
python -m unittest discover -s tests -v
python scripts/conformance.py -- python -m oaff.cli verify '{file}' --json
```

Discuss incompatible changes before implementation. The maintainers will
record the decision and version impact in the PR; a major version changes
the meaning of existing fields, while a minor version may add optional fields
without changing existing meanings. A merged PR is not a ratified standard
or a released package. Ratification requires a versioned spec, passing public
conformance corpus, documented limits, and an independently built producer or
consumer demonstration.

Please do not submit customer documents, credentials, raw private traces, or
other data you are not authorized to publish.
