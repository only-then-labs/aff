# OAFF v0.1 fixtures

`valid/` packages must pass the schema, JCS digest, and local binding
checks. They are synthetic examples; receipt attribution and evidence
statements are **illustrative, not authenticated or factually verified**.

| File | Point illustrated |
| --- | --- |
| `candidate-valid.aff` | Candidate Finding with restricted evidence and no receipts. |
| `admitted-valid.aff` | Same Finding revision with an attributed support assessment and originating Human Approval. |
| `withdrawn-valid.aff` | Same immutable revision with an appended withdrawal receipt. |
| `revision-valid.aff` | New revision linked to the earlier revision of the same Finding. |
| `conflicting-evidence-valid.aff` | Two opposing excerpts; support remains indeterminate. |
| `unavailable-evidence-valid.aff` | Source cannot be inspected; package remains structurally valid. |
| `successful-run-finding-valid.aff` | A successful run supports a bounded positive observation. |
| `failed-run-finding-valid.aff` | A failed run supports a bounded negative observation; failure does not invalidate the package. |

The two run examples use tiny synthetic bytes in `sources/`. A receiver can
check each source digest locally with `oaff verify PACKAGE --evidence ID=FILE`.
Neither package contains a full run trace or asserts that the example is true.

`invalid/` exercises schema and binding failures. Expected outcomes are in
`manifest.json`. Passing JSON Schema alone is insufficient for digest and
cross-reference failures. The fixture script is a contract check, not the
independent verifier planned for O2.
