# Proofpress → OAFF v0.1 mapping

This is a **design map for planned O3 export**, not a claim that Proofpress
already emits OAFF. It was checked against Proofpress main commit
[`47614fa`](https://github.com/chenmingtang830/proofpress/commit/47614fa7934488de1d7731be67b2d974563b2070)
on 29 September 2026. The Proofpress event ledger remains authoritative for
Proofpress; an OAFF package is a bounded external projection.

| OAFF field | Existing Proofpress source | Export rule / gap |
| --- | --- | --- |
| `finding.statement` | Immutable claim `statement` | Copy exact statement, without a generated summary. |
| `finding.id` | Claim `id`; explicit `qualifiers.revision_of` lineage where present | Mint a stable, exporter-owned URI for the root of a **validated** revision chain. If no revision link exists, one claim forms one Finding. Retain the raw claim ID in a namespaced extension. Do not merge claims by text similarity. |
| `finding.revision` | Immutable claim `id` plus claim `digest` | Derive a distinct URI from exact claim identity and digest. Never reuse it if bytes differ. |
| `finding.type` | Claim `profile` and `qualifiers` | Map only explicitly understood profile types; default to `observation` for a general assertion, documenting that descriptive choice. No inference of skill efficacy. |
| `finding.applicability` | Claim `applicability`, optional legacy `scope`, expiry and qualifiers | Carry documented validity conditions and exclusions. If the existing record lacks a usable condition, do not silently invent one; O3 needs an explicit exporter policy or a new candidate with scope. |
| `finding.producer`, `created_at` | Claim `proposer`, `created_at` | Preserve attribution. Existing self-asserted identity is not upgraded to authenticated identity. |
| `finding.evidence[]` | Claim `evidence_refs`; selected evidence records and content-addressed adapter receipts | Project bounded source URI, locator, digest, excerpt, and availability only where the adapter supplies a defensible meaning. A Proofpress evidence-record digest is **not automatically** a digest of remote source bytes; if exact source-content digest is unavailable, O3 must mark the record non-exportable or establish an explicit digest profile. Never put raw traces, secrets, or protected bytes into the package. |
| `receipts` — integrity/support | Deterministic evaluation, optional model/Jev advice, evidence receipts | Preserve method, result, input claim version, actor, policy/model version where known. Advice is attributed assessment, not admission. OAFF v0.1 has only a bounded explanation; richer Proofpress fields require a namespaced extension. |
| `receipts` — adoption | `claim_admitted`, `claim_rejected`, `claim_auto_admitted` events | Export Human Approval as `human_approval`, Owner-policy admission as `owner_policy`. Never label an automatic decision as human review. Record original policy/authority identifiers in an extension without assuming a receiver honors them. |
| `receipts` — lifecycle | Withdrawal, supersession, relation retirement, reassessment events | Export only events that bind to this exact claim revision and are authorized in the originating ledger. The receiver re-evaluates current status locally. |
| `finding.links` | Explicit revision, supersession and `depends_on` relation records | Preserve direction and exact target identities. Do not redirect dependencies to a replacement automatically. |
| Later O6 use/outcomes | Context receipts, reliance records, output references, observations | Leave out of v0.1 core Finding package until separately specified; a recorded use or outcome never proves causal improvement. |
| Package `integrity` | OAFF export serialization | New JCS/SHA-256 package digest. It does not replace the Proofpress ledger head, event hashes, or workspace-history export. |

## Export blockers to resolve in O3

1. Choose an organization-controlled URI namespace that is stable without
   publishing customer workspace IDs or access-bearing URLs.
2. Define an explicit digest profile for each supported evidence adapter.
   Where the available digest binds a receipt rather than remote source bytes,
   the exporter must not relabel it as `content_digest`.
3. Decide how to project claims with insufficient applicability conditions.
   OAFF's required condition is a deliberate constraint; a guessed condition
   would make cross-system reuse unsafe.
4. Use the Proofpress ledger head as an exporter audit reference in a
   namespaced extension, while preserving the OAFF package digest as the
   portable integrity check.

Import belongs to O4. A foreign admission receipt is a claim about the
originating organization; it does not create Proofpress governed context.
