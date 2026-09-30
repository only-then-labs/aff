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

To turn an existing note or run summary into a proposed Finding, write its
conclusion and scope explicitly. For example:

```sh
aff capture --source postmortems/oom.md \
  --source-uri https://example.org/notes/oom \
  --output oom.aff \
  --statement 'Batch size 64 exhausted memory on accelerator A.' \
  --applicability 'Training with the same model and accelerator configuration.' \
  --condition 'Batch size 64' --condition 'Accelerator A' \
  --producer-id tag:example.org,2026:human/researcher --producer-kind human
aff verify oom.aff --evidence source-1=postmortems/oom.md
aff collection add oom.aff
aff collection check
```

`capture` hashes the exact source bytes and writes only their digest and the
explicit Finding fields. It does not extract a conclusion with a model, copy
the note into the package, authenticate the producer, or authorize reuse.
The source URI must be an absolute URI chosen by the producer; use a stable
Git or document link when one exists. The default evidence availability is
`restricted`. Verify the local source bytes before distributing the package;
the recipient can check them only if it obtains the same bytes. A new capture
creates a new Finding ID and revision, so revising an existing Finding needs
an explicit revision workflow rather than re-running this command.

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
