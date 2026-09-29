# Open Agent Findings Format — v0.1 draft

Status: **draft for implementation review**. Normative requirements use
**MUST**, **SHOULD**, and **MAY** in their usual RFC 2119 sense. This document
and [the schema](../schema/oaff-0.1.schema.json) define OAFF v0.1 together.
Where JSON Schema cannot express a cross-field invariant, this document is
normative. The [fixtures](../fixtures/README.md) illustrate both.

## 1. Purpose and boundary

A **Finding** is one bounded, reusable conclusion from agent or human work.
It is atomic when it can be assessed, adopted, revised, or withdrawn
independently. A Finding can be a candidate, be rejected, or have an
originating organization's approval; OAFF does not grant permission to rely
on it in a receiving organization.

OAFF v0.1 exchanges a **package snapshot** in one `.oaff.json` file. A
snapshot contains exactly one immutable Finding revision and zero or more
attributed receipts. A later package MAY carry more receipts for the same
revision; it then has a different package digest. Rewording the statement,
scope, producer, or evidence requires a new revision identifier. OAFF does
not define a discovery service or a network protocol.

## 2. Package shape and identity

The top-level object has `oaff_version`, `finding`, `receipts`, and
`integrity`. It MAY have `extensions`. `oaff_version` MUST be `0.1.0`.
The `finding` contains:

- `id`: a globally scoped URI for the logical Finding; stable across revisions.
- `revision`: a globally scoped URI for these immutable Finding bytes. A
  producer MUST NOT reuse it for a different canonical Finding value.
  Receivers MUST treat different canonical Finding values for the same
  revision URI as an identity conflict.
- `statement`: one conclusion. A compound statement that can be independently
  falsified in parts SHOULD be split into separate Findings.
- `type`: `observation`, `procedure`, or `constraint`. These are descriptive
  labels, not proof or authority.
- `applicability`: a plain-language description, at least one condition under
  which reuse is intended, and optional exclusions. The receiver must still
  decide whether its actual task fits.
- `producer` and `created_at`: attributed origin, not authenticated identity.
- `evidence`: one or more bounded source descriptors. The source bytes need
  not be included in the package.
- `links`: optional revision or dependency references.

All identifiers in v0.1 are absolute URIs. A `urn:uuid:` URI is suitable for
examples; producers MAY use their own URI namespace. URI equality is exact
string equality. Producers MUST NOT place credentials or access tokens in
identifiers or source URIs. Timestamps are RFC 3339 UTC strings ending in `Z`.

An evidence descriptor has a package-local `id`, `source_uri`, SHA-256
`content_digest` of the exact source bytes as understood by the producer,
`availability` (`public`, `restricted`, or `unavailable`), and optionally a
bounded `locator` and `excerpt`. Its digest binds source content, while an
excerpt helps a reviewer inspect a limited projection. Neither proves the
source is authentic, reachable, or supportive. `restricted` and `unavailable`
MUST remain visible to the receiver; absence of source bytes is never a pass.

`links` can be `revision_of`, `supersedes`, or `depends_on`. `revision_of`
MUST point to an earlier revision of the same Finding `id`; the package
MUST NOT point to itself. `supersedes` and `depends_on` MAY point to another
Finding. Links are attributed assertions until the receiver checks the
referenced records and authority. A dependency that cannot be resolved MUST
NOT be treated as satisfied merely because the link is present.

## 3. Receipts and trust

Each receipt has an `id`, `kind`, `subject_revision`, `issuer`, `issued_at`,
`method`, and `result`. `subject_revision` MUST equal the package's
`finding.revision`. Receipt IDs MUST be unique within a package. A receipt
MAY cite package-local evidence IDs in `evidence_refs` and MAY include a
bounded explanation. Unknown evidence IDs are invalid.

| Kind | Allowed results | Meaning |
| --- | --- | --- |
| `integrity_check` | `pass`, `fail`, `indeterminate` | A named check of bytes, references, or origin. |
| `support_assessment` | `supported`, `unsupported`, `indeterminate` | An attributed assessment of evidence support. |
| `adoption_decision` | `admitted`, `rejected` | An originating authority's decision; never automatically a receiver's decision. |
| `lifecycle` | `withdrawn` | An attributed update to availability for reuse. |

An `adoption_decision` MUST state `authority_basis` as `human_approval` or
`owner_policy`. The latter means an originating Owner policy authorized a
bounded system decision; it is not human review of that Finding. Every
issuer is a claimed actor in the file. OAFF v0.1 provides no built-in
signature or organization identity federation. A receiver MUST NOT infer
that a named issuer was authenticated, that a support assessment proves
truth, or that foreign admission grants local authority.

The package itself has no single `verified` or `current` boolean. A receiving
implementation SHOULD report separately: schema and digest integrity;
evidence availability and any checks it can actually perform; attributed
support; and its own local adoption and lifecycle state. If a check cannot be
performed because source bytes are restricted or unavailable, report
`indeterminate`, not `pass` or `fail`.

The latest lifecycle state requires an authenticated, ordered set of receipts
and local policy. File order alone does not establish which issuer has
authority to withdraw a Finding. O5 will define cross-system lifecycle
exchange; the v0.1 file can already represent the event without pretending
to settle external authority.

## 4. Integrity and canonicalization

`integrity.algorithm` MUST be `sha-256-jcs`. To calculate the digest:

1. Remove the **top-level** `integrity` member only.
2. Canonicalize the remaining JSON value with [RFC 8785 JCS](https://www.rfc-editor.org/rfc/rfc8785).
3. Hash those UTF-8 bytes with SHA-256.
4. Encode the digest as lowercase hexadecimal in `integrity.digest`.

Receivers MUST reject duplicate JSON object keys and input that is not
valid I-JSON/JCS before hashing. They MUST compare the calculated digest to
the recorded value. Changing any Finding content, receipt, link, or extension
invalidates the digest. The digest detects accidental changes to the JSON
value when compared with a trusted copy of the digest. An attacker who can
replace both package and digest can compute a new matching digest. OAFF v0.1
does not authenticate who made the package. The source digest uses
the original source bytes, not JCS, unless the source's own contract says so.

Arrays retain their supplied order in JCS. Producers SHOULD order evidence,
links, and receipts consistently to avoid unnecessary package-digest churn.
No consumer may reinterpret an unknown extension as a check or authority
receipt. An extension key MUST be an absolute URI controlled by its publisher;
an implementation MUST preserve unknown extension values on round trip.

## 5. Validation and safe handling

A parser MUST report at least these separate classes of result:

- `invalid_json`: malformed JSON, duplicate keys, or invalid I-JSON/JCS input.
- `invalid_schema`: the document does not satisfy the v0.1 schema.
- `invalid_binding`: a digest mismatch, conflicting revision identity,
  unknown receipt evidence reference, wrong receipt subject, or invalid link.
- `indeterminate_evidence`: the package is structurally valid but named source
  bytes or an external authority cannot be checked.
- `evidence_mismatch`: the caller supplied source bytes and their SHA-256
  digest differs from the descriptor; the supplied evidence check fails.

The first three are invalid package outcomes. `evidence_mismatch` is a failed
source check. `indeterminate_evidence` is a valid package with an explicit
verification limit. A receiver MAY add more
specific diagnostics. It MUST NOT silently turn any of them into an
admission decision.

Readers SHOULD impose reasonable size, nesting, and string limits before
processing untrusted packages. They MUST treat source URIs and locators as
data; a verifier MUST NOT automatically fetch arbitrary URIs, execute
payloads, or expose private source bytes. A package SHOULD carry only the
minimum bounded excerpt needed for review. Secrets and raw private traces
MUST NOT be embedded.

## 6. Compatibility and evolution

The schema closes standard objects to unknown fields. Additional data goes
under `extensions`, keyed by absolute URI. A v0.1 reader MUST reject an
unknown `oaff_version`; it MAY retain the bytes for later processing.
Future minor versions may add optional fields without changing the meaning
of existing fields. A future incompatible change needs a new major version.

OAFF does not require OKF, Proofpress, or any particular model, database,
transport, or review service. A Markdown view may display a package but is
not an authoritative second serialization. A future OAFP may define live
exchange once multiple implementations need it.

## 7. Worked example

[candidate-valid.oaff.json](../fixtures/valid/candidate-valid.oaff.json)
contains one scoped, evidence-referenced Finding. Its package digest is
computed by the rule above. Other fixtures show an originating decision,
withdrawal receipt, restricted evidence, and deliberately invalid packages.
The fixture check validates all examples but does not evaluate whether their
illustrative statements are true.
