# AFF capture policy

This starter policy guides people and agents using this repository. Edit it to
fit your team's work. It is an instruction document, not a technical access
control or an approval receipt.

AFF's workflow is **propose → verify → local admit or reject → revise or
withdraw → use and observe**. The CLI currently supports creating candidates,
mechanical verification, and Git collection management. It does not issue
authorized admission or withdrawal decisions. Name your team's decision owner
and approval channel before treating a Finding as approved for reuse.

## Before a related task

- Read `aff/index.md` and inspect potentially relevant packages. Check the
  Finding's conditions and exclusions against the current task.
- If the source bytes are accessible, run `aff verify PATH --evidence
  source-1=SOURCE_PATH` (or provide the matching evidence IDs). If they are
  inaccessible, keep that limit visible. Do not treat package integrity as
  support for the conclusion.
- Record what was used or rejected in the task's normal work record. Do not
  infer that an origin receipt grants local approval.

## When to capture

- Capture one bounded, reusable conclusion from a successful or failed run,
  experiment, incident, or repeated workflow observation when a source record
  exists and its applicability can be stated.
- Keep the original source where the team already stores it. Choose an
  absolute `--source-uri` that the intended readers can understand. The AFF
  package binds the source's exact bytes but does not copy them.
- State a concrete conclusion, at least one applicability condition, and
  exclusions where known. Use a real producer ID and kind. If a model proposes
  the wording, review it against the source before sharing.

## When to skip or defer

- Do not capture every run, raw trace, guess, duplicate, or conclusion whose
  scope cannot yet be stated. A failed run is evidence; its reusable lesson is
  the Finding.
- Do not publish secrets, private source text, or source URIs that disclose
  information to unintended readers. The default evidence availability is
  `restricted`; choose `public` only when the source itself is approved for
  public access.
- Do not use `aff capture` to overwrite or silently revise an existing
  Finding. It creates a new ID and first revision. Preserve existing packages
  and use an explicit revision workflow when one is available.

## Before committing or sharing

1. Run `aff verify NEW.aff --evidence source-1=SOURCE_PATH`.
2. Review the generated statement, conditions, source URI, producer, and
   evidence availability. Verification does not decide whether they are true.
3. Run `aff collection add NEW.aff` and `aff collection check`.
4. Review the `.aff` file and generated `aff/index.md` in a Git pull request.
   A receiving team decides for itself whether to use the Finding.

## Decisions and lifecycle

- A person or system with explicit local authority decides admission or
  rejection for an exact revision. An agent's proposal, a successful
  `aff verify`, or a merged Git PR does not by itself grant that authority.
- Preserve previous packages when changing a Finding. `aff capture` is only
  for a new Finding; a future revision needs the same Finding ID, a new
  immutable revision ID, and an explicit relation to its predecessor.
- Treat a withdrawal as an attributed lifecycle statement. Before changing
  local use, authenticate its issuer and record your own decision. Do not
  silently delete history or assume a received withdrawal is authoritative.
- If your team needs enforced local admission, withdrawal propagation, and
  exact-revision use tracking, choose a governance system such as Proofpress.
