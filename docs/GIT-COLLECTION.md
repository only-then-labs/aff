# Git-native AFF collection

An `aff/` directory is the default distribution shape for a small collection.
It is a convention around `.aff` package files, not a change to the OAFF v0.1
wire contract. A repository can still keep its Markdown notes, post-mortems,
source documents, and code where they already live.

```text
aff/
  index.md             # generated navigation; commit this file
  findings/
    <package-digest>.aff
```

Run `aff collection init` from the repository root. Use `aff collection add
PATH` to check and copy an existing package without changing its bytes. The
package's canonical digest becomes its filename, so repeating the add is
idempotent; later receipt snapshots of the same immutable revision get distinct
files. `aff collection index` scans manually copied packages and rebuilds the
index. `aff collection check` verifies every package and detects a stale index;
run it in CI or before a pull request. All commands accept `--root PATH` when
the collection is outside the default `aff/` directory.

Packages can also be arranged in subdirectories under `findings/`. Both `.aff`
and legacy `.oaff.json` filenames are accepted. File paths organize the
collection; the Finding ID, revision, evidence binding, and links are defined
by package content. The index includes every retained snapshot and deliberately
does not call one "latest," "approved," or "safe to use." A package may pass
integrity checks while source bytes, issuer identity, links, or local authority
remain indeterminate. No source URIs are fetched during indexing.

`aff collection add` and `aff collection check` reject malformed packages,
digest mismatches, conflicting immutable revisions, and unsafe symlink package
paths. Git history and pull requests can review collection changes. A receiving
team still decides whether a Finding applies and whether to adopt it locally.
Proofpress is one governed receiver, not a required registry for AFF.

The [example collection](../examples/git-collection/aff/index.md) contains
synthetic successful- and failed-run Findings. It is a navigation example, not
an admitted knowledge base.
