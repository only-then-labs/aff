# Try AFF with your team

AFF is an Apache-2.0, v0.1 **draft** for turning a bounded agent or human
learning into a portable Finding with evidence and applicability. It is ready
for outside design-partner trials, not a claim of ratified-standard adoption.

## Five-minute synthetic trial

Requires Python 3.10+ and Git:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install 'git+https://github.com/only-then-labs/aff.git@v0.1.0a1'
.venv/bin/aff demo
cd aff-demo
../.venv/bin/aff collection check
```

Read `aff/index.md`, the two linked `.aff` candidates, and their source notes
under `notes/`. Compare the successful and failed run: both use the same
Finding contract, but their conditions differ. Run `aff verify PACKAGE
--evidence source-1=notes/NAME-run.md` with the correct package and note to
check a source digest. The notes and packages are synthetic and unapproved.

## Try your own note

In a repository containing a post-mortem or run summary, run `aff init`, review
the generated `AGENTS.md` and `aff/policy.md`, then follow [Getting
started](GETTING-STARTED.md) to capture one conclusion, verify source bytes,
and add the package to `aff/`. Existing `AGENTS.md` and policy files are never
overwritten. Do not put private notes or source links into a public repo.

Ask a colleague or agent who did not write the Finding to locate it through
`aff/index.md`, decide whether its conditions fit a later task, and explain
what evidence it could actually inspect. The [outside trial guide](OUTSIDE-TRIAL.md)
lists the observations that would help refine this format and workflow.

## Where governance lives

The [AFF governance model](GOVERNANCE.md) distinguishes proposal, technical
verification, support assessment, local admission or rejection, revision,
withdrawal, and use. The standalone CLI implements candidate capture,
mechanical checks, and Git collection management. It does not authenticate an
issuer or grant local authority. A team may review files in Git, but a merged
PR is not an AFF admission decision.

[Proofpress](https://github.com/chenmingtang830/proofpress) is the Apache-2.0
reference product for enforced local governance. Its [local
quickstart](https://github.com/chenmingtang830/proofpress#quick-start) shows
synthetic claim proposal, Owner review, Human Approval, and governed-context
retrieval. Its [AFF export guide](https://github.com/chenmingtang830/proofpress/blob/main/docs/OAFF_EXPORT.md)
shows how a bounded Proofpress claim can be projected into `.aff`. These are
separate installations today, and the complete cross-system revision and
withdrawal loop is not yet a one-command workflow.

## Feedback we want

- Could you write one Finding from an existing successful or failed run without
  inventing evidence or scope?
- Would a later agent find and apply it correctly through the index?
- Which fields or commands added work without helping the team?
- Would Git review suffice for your use, or is an authorized local decision,
  withdrawal response, or use record missing?

Use a [GitHub issue](https://github.com/only-then-labs/aff/issues) for
non-sensitive feedback or a minimal synthetic case. Do not post credentials,
private source material, or raw customer traces.
