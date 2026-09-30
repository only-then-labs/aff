# Failed run to Finding: v0.1 coverage and loss report

Status: synthetic contract examples, not a production export. The paired
[successful](../fixtures/valid/successful-run-finding-valid.aff) and
[failed](../fixtures/valid/failed-run-finding-valid.aff) examples use the
same OAFF v0.1 schema. Each Finding states one bounded conclusion; the source
run is evidence. A failed run alone does not automatically create a Finding.

Proofpress's R&D Blueprint compiler can create a `failed-attempt` claim
qualifier. Its [source](https://github.com/chenmingtang830/proofpress/blob/main/src/proofpress/integrations/research_blueprint.py)
includes the fields below. The current [OAFF exporter](https://github.com/chenmingtang830/proofpress/blob/main/src/proofpress/oaff_export.py)
exports the claim statement, explicit applicability and verified retrieval
evidence, but does not inspect or project the qualifier. It labels every
exported Finding `observation`.

| Blueprint source | OAFF v0.1 projection today | Information lost or requiring manual prose |
| --- | --- | --- |
| Claim statement and applicability description/conditions | `finding.statement` and `finding.applicability` | Only explicitly written content survives. The exporter does not infer a failure-specific scope. |
| Bound retrieval evidence with supplied exact bytes | `finding.evidence[]` with source URI and digest | Run trajectory and private source bytes do not travel; the receiver gets a restricted descriptor. |
| `claim_kind: failed-attempt` | `finding.type: observation` | Structured failure classification is lost. A receiver may read a failure from statement prose, but cannot query the original qualifier. |
| `experiment` identity, model/dataset/config digests | None | Experiment identity and configuration linkage are lost unless the producer deliberately states them in existing fields. |
| `failure.intervention` and `expected_outcome` | None | Planned action and expectation are lost as structured values. |
| `failure.observed_outcome` and `feedback_evidence_refs` | Evidence descriptor only if included as a bound claim evidence ref | Observation wording and mapping from feedback to each source are lost as structured values. |
| `failure.invalidated_hypotheses` | None | Which hypotheses were ruled out is lost. |
| `failure.repeat_policy`, `changed_dimension_required`, `next_action` | None | Retry boundary and next action are lost unless the claim statement/applicability says them explicitly. |
| Human or Owner-policy admission, linked withdrawal | Attributed receipts when available and bound by the exporter | Origin decision is visible but never becomes receiving authority. Other lifecycle history is outside this exporter. |

This is a **loss report**, not an AFF extension proposal. The v0.1 core is
outcome-neutral and can already exchange a negative conclusion with source
evidence. An optional namespaced extension may be appropriate if real
receivers need the Blueprint fields; any extension must preserve unknown
values without gaining authority. A core field requires evidence from
independent handoffs, a versioned migration, and conformance cases. Do not
make an enum for success/failure before deciding whether it describes the
source run, the Finding's truth status, or a later reuse outcome.
