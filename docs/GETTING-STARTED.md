# Start using AFF in an existing repository

AFF v0.1 is a draft open format. You can use it locally today without a
Proofpress account. The current integration is a Python CLI plus ordinary
repository files; it is not an automatic agent plugin. Python 3.10+ and Git
are sufficient for this path.

## 1. Install the CLI

From a shell with Python 3.10+:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install 'git+https://github.com/only-then-labs/aff.git'
.venv/bin/aff --help
```

This installs the current draft from GitHub. For a repeatable team setup, pin
the Git URL to an audited commit in your dependency file. The Python package
name and import path are `oaff`; the command users run is `aff`.

## 2. Initialize your repository

Run from the root of the repository that holds your notes or run records:

```sh
aff init
```

This creates `aff/findings/`, a generated `aff/index.md`, a starter
`aff/policy.md`, and an `AGENTS.md` that tells an agent when to read and
propose Findings. Read and edit the policy for your team. If `AGENTS.md` or
`aff/policy.md` already exists, `aff init` keeps it. Add a short pointer to
`aff/policy.md` in your existing `AGENTS.md`; the command prints that reminder.
Running `aff init` again checks an existing index rather than overwriting it.

These Markdown instructions guide a cooperating agent; they do not install a
background watcher or enforce an approval policy. The generated index is a
discovery aid, not a list of Findings approved for use.

The complete governance sequence is **propose → verify → local admit or reject
→ revise or withdraw → use and observe**. This first-run guide covers the
candidate and mechanical-check steps. The [governance model](GOVERNANCE.md)
separates the format's lifecycle vocabulary from workflows the CLI actually
implements.

## 3. Capture one learning

Keep your original post-mortem, experiment note, or run summary in place.
Decide on **one** conclusion that a later run could use. For example:

```sh
aff capture \
  --source postmortems/oom.md \
  --source-uri https://github.com/ORG/REPO/blob/COMMIT/postmortems/oom.md \
  --output oom.aff \
  --statement 'Batch size 64 exhausted memory on accelerator A.' \
  --applicability 'Training this model on accelerator A.' \
  --condition 'Batch size 64' \
  --condition 'Same model and accelerator configuration' \
  --exclusion 'A different accelerator is used' \
  --producer-id tag:example.org,2026:human/researcher \
  --producer-kind human
```

Replace the example source URI and producer ID with real values for your team.
The source URI must be absolute; choose a link the intended readers may use.
The package contains a digest of the exact source bytes, not the note itself.
The default source availability is `restricted`. A failed run and a successful
run use the same command and format; the Finding is the reusable conclusion,
while the run is evidence. The CLI does not infer that conclusion for you.

## 4. Verify, collect, review

```sh
aff verify oom.aff --evidence source-1=postmortems/oom.md
aff collection add oom.aff
aff collection check
git add AGENTS.md aff/
```

Review `aff/index.md`, the new `.aff`, and your original note in a normal
pull request. `aff verify` checks shape, package integrity, and the source
digest when you supply source bytes. It does not prove that the conclusion is
true, authenticate the named producer, or authorize another team to rely on
it. The Git collection accepts `.aff` and older `.oaff.json` files.

## 5. Use it in later agent work

An agent following the generated `AGENTS.md` reads `aff/index.md` before a
related task, opens relevant packages, checks their conditions and exclusions,
and tells you what it used or rejected. If your agent does not automatically
read `AGENTS.md`, point its repository instructions at that file. No AFF Skill,
MCP server, or Proofpress account is required for this local path. Automatic
source extraction, timely retrieval, and organization-wide approval remain
separate integrations.

For the underlying behavior and limits, see the [Git collection guide](GIT-COLLECTION.md)
and [first outside trial](OUTSIDE-TRIAL.md).
