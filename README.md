# OAFF — Open Agent Findings Format

**A portable format for agent findings, with evidence and verification.**

OAFF defines a small, versioned JSON record for a conclusion an agent or human
may want to reuse. The record carries its scope, evidence references, attributed
checks and decisions, and revision history. A receiver decides for itself
whether to trust and use a finding.

This repository contains the **v0.1 draft**, not a ratified standard:

- [Normative specification](spec/OAFF-v0.1.md)
- [JSON Schema](schema/oaff-0.1.schema.json)
- [Positive and negative fixtures](fixtures/README.md)
- [Proofpress field mapping](docs/PROOFPRESS-MAPPING.md)

O1 is the format-contract milestone. The independent verifier, Proofpress
export/import, lifecycle sync, and conformance release are separate planned
milestones in the [strategy roadmap](https://app.notion.com/p/3ea1bd5e74fc81ef8ddcfef35d3d605e).

The JSON Schema validates shape. The fixture check also validates package
digests and the few cross-field invariants stated in the spec. It is **not**
an evidence evaluator, identity verifier, or adoption decision engine.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/check_fixtures.py
.venv/bin/python -m unittest discover -s tests -v
```

## Offline verifier (O2)

The Python package adds a standalone CLI and library. It never fetches a
source URI, authenticates a named receipt issuer, or grants local adoption.

```sh
oaff verify fixtures/valid/candidate-valid.oaff.json
oaff verify fixtures/valid/candidate-valid.oaff.json --json
oaff verify finding.oaff.json --evidence run-42=/path/to/source-bytes
oaff verify first.oaff.json later.oaff.json
```

The command exits **0** for a valid package, including
`valid_with_limits` when source bytes or linked revisions were not supplied;
**1** for an invalid package or supplied source digest mismatch; and **2**
for CLI usage errors. JSON output keeps package integrity, evidence-byte
checks, receipt counts, and local authority separate. Passing the verifier
never means the Finding is true, authenticated, or approved for reuse.

The format and this repository are licensed under [Apache-2.0](LICENSE).
