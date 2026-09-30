# AFF — Agent Findings Format

**A portable format for agent findings, with evidence and verification.**

AFF defines a small, versioned JSON record for a conclusion an agent or human
may want to reuse. The record carries its scope, evidence references, attributed
checks and decisions, and revision history. A receiver decides for itself
whether to trust and use a finding.

This repository contains the **v0.1 draft**, not a ratified standard:

- [Normative specification](spec/OAFF-v0.1.md)
- [JSON Schema](schema/oaff-0.1.schema.json)
- [Positive and negative fixtures](fixtures/README.md)
- [Proofpress field mapping](docs/PROOFPRESS-MAPPING.md)
- [KIP/OKF interoperability mapping and loss report](docs/KIP-OKF-INTEROP.md)
- [Conformance runner](docs/CONFORMANCE.md) and [contribution process](CONTRIBUTING.md)

The OAFF v0.1 format contract and independent verifier have merged. Proofpress export
merged in [PR #210](https://github.com/chenmingtang830/proofpress/pull/210); hosted
candidate intake and local proposal are under review in
[PR #212](https://github.com/chenmingtang830/proofpress/pull/212). Owner UI,
lifecycle sync, and independent interoperability validation remain in the
[strategy roadmap](https://app.notion.com/p/3ea1bd5e74fc81ef8ddcfef35d3d605e).

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
aff verify fixtures/valid/candidate-valid.oaff.json
aff verify fixtures/valid/candidate-valid.oaff.json --json
aff verify finding.oaff.json --evidence run-42=/path/to/source-bytes
aff verify first.oaff.json later.oaff.json
```

The command exits **0** for a valid package, including
`valid_with_limits` when source bytes or linked revisions were not supplied;
**1** for an invalid package or supplied source digest mismatch; and **2**
for CLI usage errors. JSON output keeps package integrity, evidence-byte
checks, receipt counts, and local authority separate. Passing the verifier
never means the Finding is true, authenticated, or approved for reuse.

`oaff verify` remains an equivalent command for existing scripts. AFF is the
public name; existing `.oaff.json` files, the `oaff_version` key, the Python
`oaff` import package, and the v0.1 digest contract remain unchanged. See the
[naming and compatibility decision](docs/AFF-NAMING-COMPATIBILITY.md).

## Candidate inbox (O4 foundation)

`CandidateInbox` retains verified foreign packages in a local SQLite store.
It partitions them by a workspace key supplied by the **already authenticated
caller**, accepts later receipt snapshots for the same immutable Finding,
deduplicates repeats, and quarantines invalid or conflicting bytes. Every
result has `local_authority: none`; the inbox has no adoption operation.
`list_candidates` shows the latest receipt snapshot per revision for review;
`get_candidate` reads a selected retained snapshot. Both require the caller's
authenticated workspace key and return no other workspace's records. A selected
snapshot reports whether it is the latest retained snapshot of that revision;
receivers must not silently promote an older snapshot over newer receipts.

```python
from oaff import CandidateInbox

with CandidateInbox("oaff-inbox.db") as inbox:
    result = inbox.ingest("authenticated-workspace-id", open("finding.oaff.json", "rb").read())
    print(result["state"], result["verification"]["status"])
```

This is a reference import core, not a hosted authentication or governance
integration. The caller must enforce workspace access before invoking it and
keep the database in its own protected storage. Proofpress hosted adoption
requires its separate workspace-ownership and review gates.

The format and this repository are licensed under [Apache-2.0](LICENSE).
