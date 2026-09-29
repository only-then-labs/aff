# Proofpress → OAFF v0.1 mapping

Proofpress [PR #210](https://github.com/chenmingtang830/proofpress/pull/210)
merged a **bounded O3 exporter** on 29 September 2026. Its implementation is
documented in [Proofpress's export guide](https://github.com/chenmingtang830/proofpress/blob/main/docs/OAFF_EXPORT.md).
The Proofpress event ledger remains authoritative for Proofpress; an OAFF
package is an external projection. The table distinguishes the implemented
subset from later mapping work.

| OAFF field | Existing Proofpress source | Export rule / gap |
| --- | --- | --- |
| `finding.statement` | Immutable claim `statement` | Copy exact statement, without a generated summary. |
| `finding.id` | Immutable claim `id` | One Proofpress claim forms one Finding. The exporter derives a stable URI from the caller's organization namespace and a hash of the claim ID. It does not expose the raw ID or infer lineage. Explicit revision-chain mapping remains for O5. |
| `finding.revision` | Immutable claim `id` plus claim `digest` | Derive a distinct URI from exact claim identity and digest. Never reuse it if bytes differ. |
| `finding.type` | Claim assertion | The current exporter uses descriptive `observation`. Profile-specific types remain future work. No inference of skill efficacy. |
| `finding.applicability` | Claim `applicability.description` and `validity_conditions` | The current exporter requires both and rejects claims lacking them. Legacy scope, exclusions, and expiry are not projected. |
| `finding.producer`, `created_at` | Claim `proposer`, `created_at` | The current exporter derives an actor URI from the namespace and proposer string, retaining the recorded time. Existing self-asserted identity is not upgraded to authenticated identity. |
| `finding.evidence[]` | Claim `evidence_refs` and retrieval receipts | Every evidence reference must be a valid retrieval receipt. The caller supplies exact source bytes and an approved source URI; export checks the bytes against `source_content_digest`, then emits a restricted descriptor. It rejects unsupported or inaccessible source bytes. It omits excerpts and locators. A receipt digest is never relabeled as a source-content digest. |
| `receipts` — integrity/support | Deterministic evaluation, optional model/Jev advice, evidence receipts | Not projected by the current exporter. Future receipts must bind the exact claim revision and preserve method limits. Advice remains attributed assessment, not admission. |
| `receipts` — adoption | `claim_admitted`, `claim_auto_admitted` events | The current exporter includes a matching latest admission, labeling Human Approval `human_approval` and automatic admission `owner_policy`. Rejections and broader history are not yet projected. A receiver inherits no authority. |
| `receipts` — lifecycle | Claim withdrawal | The current exporter includes a withdrawal only when it references the included admission. Supersession, relation retirement, and reassessment remain future work. |
| `finding.links` | Explicit revision, supersession and `depends_on` relation records | Omitted in the current exporter. O5 must preserve direction and exact target identities without redirecting dependencies automatically. |
| Later O6 use/outcomes | Context receipts, reliance records, output references, observations | Leave out of v0.1 core Finding package until separately specified; a recorded use or outcome never proves causal improvement. |
| Package `integrity` | OAFF export serialization | New JCS/SHA-256 package digest. Namespaced extensions record the Proofpress ledger head and export time for audit. This does not replace event hashes or workspace-history export. |

## Current export boundary

The caller chooses an organization-controlled HTTPS namespace and source URI.
The exporter checks the exact bytes at export time and fails closed on missing
source bytes, missing applicability conditions, or unsupported evidence. A
receiving implementation should still inspect the source's availability and
authenticate any receipt issuer under its own policy. The exporter does not
sign the package or include private source bytes.

The OAFF [candidate inbox](../README.md#candidate-inbox-o4-foundation) is an
O4 storage foundation. Proofpress hosted import and local adoption are not
implemented here. A foreign admission receipt does not create Proofpress
governed context.
