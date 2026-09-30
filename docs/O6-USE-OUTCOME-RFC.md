# O6 RFC: declared use and observed outcome

Status: **design proposal, not part of AFF/OAFF v0.1 conformance**. This page
fixes the first testable product boundary before a wire schema is chosen.

## Decision proposed

Keep the immutable Finding package about **what was learned**. Represent
later use and later observation as separate, append-only attributed records
linked to an **exact Finding revision and package digest**. A source run's
success or failure is evidence for the Finding; an outcome after reuse is a
different event. Neither a use record nor an outcome is proof that the
Finding was true, locally authorized, or causally responsible for a result.

The first implementation should export a use record from a receiver's actual
context/reliance event, then an outcome record only when a separately observed
result exists. It should not manufacture a use because a Finding appeared in a
prompt, nor manufacture an outcome from the source run that produced it.

## Candidate record model

The fields below are a review target, not reserved v0.1 keys or a promise of
the final JSON names.

| Record | Required information | Meaning and limit |
| --- | --- | --- |
| `declared_use` | Record URI; exact Finding ID, revision URI and package digest; attributed actor and time; purpose; receiver-local context or task reference; optional local decision and output references | The actor says this exact revision was used in a bounded task. A context display alone is weaker than declared reliance. Foreign local-decision references are historical attribution, not destination approval. |
| `observed_outcome` | Record URI; exact use-record URI and digest; attributed observer and time; bounded observation; evidence descriptor or explicit unavailable state | A later result associated with a use. It does not assert counterfactual improvement or causality. Multiple outcomes can reference one use; a correction creates a new record. |

Every cross-record reference should bind an immutable digest as well as an ID.
The exchange package should have its own JCS/SHA-256 integrity rule, bounded
sizes, explicit version, and optional namespaced extensions. A receiver
validates the reference graph but treats actor identities as claims until
authenticated by its own policy. This design intentionally avoids adding
`used: true` or `successful: true` to the Finding itself.

## Producer and receiver behavior

1. Proofpress can project a real local context/reliance event and its output
   reference into `declared_use`; the export must not expose prompt bodies,
   raw traces, private output, credentials, or workspace-local IDs that are
   unsafe to share. A consumer may store only opaque references and digests.
2. A separately observed later run, evaluation or human review may create an
   `observed_outcome`. It records observation method, source availability and
   limits. If the evaluator did not inspect the later output, report
   indeterminate rather than improvement.
3. The destination links a received use/outcome to the exact received
   Finding revision. If the package or use record is absent, keep an explicit
   unresolved reference; never silently bind by title or by latest revision.
4. A source's local approval, use, or outcome never transfers local authority.
   An imported outcome is historical evidence, not the receiver's grade.
5. A later withdrawal keeps historical uses visible but triggers local
   lifecycle review before further reuse. O5 defines that decision path.

## Evaluation before versioning

- Export three real, consented cases: correct in-scope use, out-of-scope use,
  and a documented failed run that a later agent avoided. Keep private source
  bytes out of the public corpus.
- A clean receiver reconstructs **which exact revision was used, in which
  task, by whom, and what was later observed**, without Proofpress internals.
- The same receiver distinguishes presented context from declared reliance,
  observed outcome from causal benefit, and source-run failure from a later
  task outcome. Misclassification fails the gate.
- Compare no prior context, a plain summary, and AFF handoff on the same
  downstream tasks. Report correctness, scope misuse, time, and cost. A use
  count alone is not an adoption or performance metric.

## Open design choices

- Choose a separate versioned event package versus a generic event envelope
  after inspecting actual Proofpress context and reliance receipts. Do not
  append these records to an immutable v0.1 Finding revision or hide them in
  a free-text extension.
- Decide privacy-preserving task/output reference profiles with the first
  receiving team. Avoid a global `task_id` that assumes shared infrastructure.
- Specify correction, retraction, issuer authentication and event-ordering
  before calling the records portable governance evidence.

**O6 exit:** two independent implementations can reconstruct one real
Finding → declared use → observed outcome chain from exported records, while
correctly preserving every attribution and authority limit. This RFC alone
does not meet that exit.
