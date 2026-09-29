# OAFF v0.1 fixtures

`valid/` packages must pass the schema, JCS digest, and local binding
checks. They are synthetic examples; receipt attribution and evidence
statements are **illustrative, not authenticated or factually verified**.

| File | Point illustrated |
| --- | --- |
| `candidate-valid.oaff.json` | Candidate Finding with restricted evidence and no receipts. |
| `admitted-valid.oaff.json` | Same Finding revision with an attributed support assessment and originating Human Approval. |
| `withdrawn-valid.oaff.json` | Same immutable revision with an appended withdrawal receipt. |
| `revision-valid.oaff.json` | New revision linked to the earlier revision of the same Finding. |
| `conflicting-evidence-valid.oaff.json` | Two opposing excerpts; support remains indeterminate. |
| `unavailable-evidence-valid.oaff.json` | Source cannot be inspected; package remains structurally valid. |

`invalid/` exercises schema and binding failures. Expected outcomes are in
`manifest.json`. Passing JSON Schema alone is insufficient for digest and
cross-reference failures. The fixture script is a contract check, not the
independent verifier planned for O2.
