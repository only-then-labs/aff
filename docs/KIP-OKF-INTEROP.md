# AFF ↔ KIP / OKF: mapping and loss report

Status: O8 baseline, 30 September 2026. This compares public source revisions,
not customer installations or a claimed certified conversion:

- [KIP 2.0 Capsule specification](https://github.com/ldclabs/KIP/blob/69a05ff71e5c1ef759311432151b1a28d6aa749a/KIP-2.0-Capsule-Specification.md)
  and [element schema](https://github.com/ldclabs/KIP/blob/69a05ff71e5c1ef759311432151b1a28d6aa749a/schemas/kip-element.schema.json)
  at `69a05ff` (2.0-draft).
- [OKF specification](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/SPEC.md)
  at `ad30107` (v0.2).
- [AFF/OAFF v0.1](../spec/OAFF-v0.1.md) and the paired
  [successful](../fixtures/valid/successful-run-finding-valid.aff) /
  [failed](../fixtures/valid/failed-run-finding-valid.aff) run Findings.

## Unit of exchange and authority

AFF packages one immutable Finding revision and attributed receipts. The
Finding is the bounded learning; the run is a possible evidence source. KIP's
native unit is a governed cognitive-state element in a Space; a Capsule carries
selected state or ordered changes. OKF's native unit is a Markdown concept in
a directory bundle. Both can express related information. None of these units
is an exact alias for another. KIP explicitly keeps Capsule bytes separate
from destination mutation authority; OKF trust tiers are advisory, not access
control. AFF also requires a receiver-local adoption decision.

## Field mapping: AFF → KIP 2.0 Capsule

This is a candidate semantic decomposition, **not an implemented converter**.
KIP requires schema, identity resolution, closure, and destination Governance;
string copying would produce a misleading Capsule.

| AFF v0.1 | Possible KIP location | Loss or required decision |
| --- | --- | --- |
| `finding.id`, `revision` | Source element identity and Capsule source mapping | A destination element ID must be chosen locally. AFF revision URI is not a KIP Space sequence or Capsule-local ID. |
| `statement`, `type` | Proposition plus an assertion, or an installed Schema Package profile | AFF's bounded natural-language conclusion has no automatic KIP predicate/object, stance, or schema mapping. The AFF type enum is not a KIP element kind. |
| `applicability` | Assertion context/valid time or profile-specific facets | Plain-language conditions and exclusions have no faithful machine-evaluable translation. |
| `producer`, `created_at` | Attributed assertion/activity origin | Claimed AFF origin is not an authenticated KIP actor or local governance principal. |
| `evidence[]` | Evidence elements, external references, or blobs | AFF source digest and availability may be preserved, but locator/excerpt, provenance closure, and KIP redacted versus unavailable need explicit handling. AFF `restricted` does not by itself prove redaction. |
| `receipts[]` | Historical evidence/activity or governance records | AFF attributed support/adoption/withdrawal cannot become destination trust, grades, or mutation authority. Ordering and issuer authentication remain unresolved in AFF v0.1. |
| `links[]` | Typed references or profile-defined relations | Identity mapping and closure must be checked. A present AFF dependency cannot be treated as resolved. |
| `integrity` | Capsule digest and optional proofs | AFF JCS package digest is for different bytes. A new Capsule digest must be computed; neither digest authenticates the producer by itself. |

KIP Capsule export/import has snapshot/delta, source and destination identity
separation, external references, and a verify → validate → preview →
Governance → import path. A working adapter would need to choose a KIP schema
profile, create a loss report per record, and validate the result with KIP's
reference implementation. We do not publish a mock Capsule as a passing vector.

## Field mapping: AFF → OKF v0.2

`oaff.interop.okf_view(package_bytes)` implements a one-way discovery view.
It verifies the AFF package first, emits a single OKF Markdown document with
JSON-syntax YAML frontmatter, and returns a machine-readable loss report. The
view uses only `type: Finding`, a title, `status: draft`, and `sources` in
frontmatter when source URIs are plain HTTP(S) URLs without embedded
credentials. Other URI forms are omitted and named in the loss report. The
statement and applicability are body text. It deliberately
omits `verified` and `generated`: neither a foreign AFF admission nor its
producer is an OKF confirmation or the actor who generated the view.

| AFF v0.1 | OKF v0.2 view | Loss |
| --- | --- | --- |
| `statement` | Title and Markdown body | Prose survives, but Markdown editing cannot preserve immutable AFF bytes. |
| `applicability` | Body description, conditions, exclusions | Conditions lose structured semantics. |
| `evidence[].id/source_uri` | `sources[].id/resource` | Digest, locator, excerpt, availability and source-byte checks are not OKF source fields; availability is only displayed as text. |
| `producer`, `created_at` | No `generated` assertion | AFF producer is not the actor who made the Markdown projection. |
| `receipts` | No `verified` or stable status promotion | An origin decision never becomes OKF human review, currentness, or receiver authority. |
| `id`, `revision`, `links`, `integrity` | Loss report only | No OKF core equivalent for AFF revision identity, typed dependencies, or package digest. |

The converter is deliberately not invertible and does not establish that the
underlying statement is true. The loss report carries AFF identity and digest
for audit, but the Markdown document is a display artifact, not a second
authoritative serialization. The output's `draft` label is a conservative
discovery status; an OKF reader still applies its own consumption policy.

## Evaluation gates

1. Collect 20–30 real, consented Findings from at least two independent
   producers, including failed and successful runs, conflicting evidence,
   revisions, withdrawals, and restricted sources. Do not include raw private
   traces in public fixtures.
2. For each format, have an independent implementer map fields, record what
   cannot be represented, and measure time to first valid import and review.
3. Test semantic preservation by asking a receiver to identify the conclusion,
   evidence, scope, origin versus local authority, and current lifecycle
   state. Count unsafe authority upgrades and lost exclusions as failures.
4. Run a downstream task twice with and without the imported Finding, then
   check whether it was used correctly and whether the result improved. Do
   not infer causality from a use receipt alone.
5. Only consider a core AFF field after repeated independent loss cases. Use a
   namespaced extension or profile first when the need is domain-specific.

Current evidence is limited to synthetic fixtures and a one-way OKF view. It
does not establish market preference, independent adoption, or KIP/OKF
round-trip interoperability.
