# AFF governance model and current tools

AFF v0.1 is a portable Finding contract **and** a vocabulary for governed
learning. It carries one immutable Finding revision plus attributed receipts
for checks, decisions, and lifecycle changes. The format does not itself
authenticate people, decide truth, grant a recipient permission to rely, or
operate a hosted workflow. Those actions belong to the team or receiving
system. The [specification](../spec/OAFF-v0.1.md) defines the wire contract.

| Stage | Meaning | Available today |
| --- | --- | --- |
| Propose | Preserve one bounded conclusion, source evidence, scope, and producer attribution as a candidate. | `aff capture` creates a new `.aff` with no approval receipts. The producer reviews the wording. |
| Verify | Check structure, package integrity, and supplied source bytes; separately assess whether the evidence supports the conclusion. | `aff verify` handles the mechanical checks and reports limits. It does not authenticate the producer or determine truth. The format can carry attributed `integrity_check` and `support_assessment` receipts, but the CLI does not issue them. |
| Admit or reject | An authorized team decides whether *its own* agents may rely on an exact revision. | The format can carry an attributed `adoption_decision` receipt with an authority basis. A received decision is never another team's local authorization. The Git CLI has no admission command or policy engine; a Git merge alone is not admission. Proofpress provides a separate local governance workflow. |
| Revise | Preserve the earlier revision and link a changed statement, scope, or evidence to a new immutable revision. | The schema defines stable Finding IDs, revision IDs, and typed links. `aff capture` creates a fresh Finding; it does not revise an existing one. Lifecycle reconciliation is incomplete. |
| Withdraw | Preserve history while signaling that a revision should no longer be offered for reuse. | The format can carry an attributed `lifecycle` receipt. A receiver must authenticate the issuer and apply its own policy. The Git CLI does not issue withdrawals or automatically stop previously admitted use. |
| Use and observe | Record exact-revision use and a later attributed observation. | This is an open design, outside the v0.1 Finding package. No causal improvement is inferred from use or outcome records. |

An agent may find candidates, draft Findings, run mechanical checks, and point
out missing evidence. It should not write a local admission on its own behalf.
A team can begin with Git for capture and review, then add its chosen local
decision workflow. Proofpress is one implementation of that governance layer;
an AFF file remains usable without a Proofpress account.

The starter [`aff/policy.md`](../src/oaff/templates/policy.md) created by
`aff init` is an instruction template for this process. It is not a security
control. Teams should state their actual decision authority before using
Findings for consequential work.
