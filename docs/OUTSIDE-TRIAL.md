# First outside AFF trial

This is a small product and interoperability trial for a team that already has
experiment notes, post-mortems, or agent run summaries. It tests whether a
bounded Finding is useful enough to keep producing and revisiting. It is not
a certification, a hosted Proofpress pilot, or evidence that AFF is a ratified
standard. Use synthetic or approved, non-sensitive material only.

## Track A: one team's existing workflow

1. Choose one source note from a successful run and one from a failed run. Keep
   the notes in their current location. Before using AFF, record where the next
   person or agent would look for a prior conclusion and whether it would find
   the relevant note.
2. For each note, state one conclusion, the conditions under which it applies,
   and at least one exclusion if the note supports one. Leave uncertain claims
   as uncertain; do not turn a run trace into an asserted general rule.
3. Follow the [Git collection guide](GIT-COLLECTION.md) to run `aff capture`,
   verify against the exact source bytes, add both `.aff` files to `aff/`, and
   run `aff collection check`. Review the package and generated `index.md` in
   a normal Git pull request. No Proofpress account is required.
4. In a later related task, ask a different person or agent to find a relevant
   Finding through `aff/index.md`. Have them say whether the scope fits the new
   task, whether they could inspect the cited source, and what they actually
   used. A valid digest is not evidence that the conclusion is true or locally
   approved.

Record: minutes to first valid Finding; fields that caused confusion; whether
the conclusion and scope needed human correction; whether source access was
possible; whether the next user found and applied it; and the work required to
keep the collection current. A team choosing to continue use is useful
qualitative evidence. Do not infer avoided work or causal model improvement
from one later task.

## Track B: an independent producer or reader

An implementer who has not imported this repository's verifier can use the
[v0.1 spec](../spec/OAFF-v0.1.md), [schema](../schema/oaff-0.1.schema.json),
and [public fixtures](../fixtures/README.md) to produce or read a `.aff`
package in another language or tool. Run the [conformance harness](CONFORMANCE.md)
against the independent reader. Exchange at least one package with the Track A
team and report what was preserved or lost: Finding and revision IDs, statement,
applicability, evidence digest and availability, links, and attributed receipts.
Do not treat a received admission receipt as the reader's own decision.

Record implementation version, language, time to first valid package, test
results, unclear spec language, field-level losses, and any safety failure.
Passing our reference CLI or making a second wrapper around it does not count
as an independent implementation. Keep the team's actual source notes and
private traces out of public issues and test fixtures.

## What closes the first gate

The first product gate is complete when an outside team has captured its own
bounded successful and failed-run Findings, reviewed them through its normal
Git workflow, and revisited at least one in later work. Report awkward or
abandoned steps as plainly as successful ones. A separate interoperability
gate needs an independently built producer or reader to pass the public cases
and perform one exchange. Neither gate requires a Proofpress deployment.
