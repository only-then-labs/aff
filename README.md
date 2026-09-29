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
```

The format and this repository are licensed under [Apache-2.0](LICENSE).
