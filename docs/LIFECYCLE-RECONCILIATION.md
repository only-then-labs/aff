# O5 lifecycle reconciliation: reviewable foundation

Status: implementation note, 30 September 2026. This does not change the
normative [OAFF v0.1 contract](../spec/OAFF-v0.1.md) or complete O5.

The candidate inbox now exposes `CandidateInbox.lineage(workspace, finding_id)`.
It returns the latest **retained receipt snapshot per immutable revision**,
the number of snapshots, claimed revision/dependency links, claimed origin
admission and withdrawal events, and whether a target revision is retained in
that workspace. The inbox accepts out-of-order older snapshots but refuses
mutated receipt IDs and incomparable receipt branches for one revision;
display selects the maximal retained receipt set. Existing inbox files are
migrated in place with receipt counts. History remains stored. The response explicitly says
`current_revision: undetermined`, `local_review_required: true`, and
`local_authority: none`; it limits output to 100 revisions and reports
`has_more`. Its row order is local ingestion order for review; ingestion order
breaks ties between equal-sized comparable receipt sets but is not a causal or
trusted lifecycle order.

This is a display and reconciliation input, never a permission to rely. For
example, the [withdrawn fixture](../fixtures/valid/withdrawn-valid.oaff.json)
claims a withdrawal of the first revision, while the
[revision fixture](../fixtures/valid/revision-valid.oaff.json) claims a later
revision. A receiver can show both without treating the later revision as
locally adopted or the foreign withdrawal as authenticated.

## Receiver decision path still required

1. Verify each package and preserve its exact digest, immutable Finding value,
   and receipt snapshot. Quarantine any conflicting bytes under one revision.
2. Authenticate the source and lifecycle issuer through a receiver-chosen
   channel or identity policy. v0.1 self-declared issuer IDs and package
   hashes alone do not do this. An unauthenticated withdrawal is an attributed
   claim requiring review, not an automatic local withdrawal.
3. Resolve `revision_of`, `supersedes`, and `depends_on` against retained
   identities. A `target_retained` flag only says that bytes are present; it
   does not establish a valid dependency or authority. Missing references
   stay unresolved.
4. Find any **local** admitted claim linked to the exact foreign revision.
   Present a re-evaluation task with the source package and verified issuer
   information. The receiver's policy decides whether to pause use during
   review; the action and reason must be recorded locally. Do not erase the
   prior admission or automatically transfer origin standing to a new
   revision.
5. After an authorized local decision, recompute dependency eligibility and
   make the current state explainable. Never silently redirect a declared use
   from the old revision to a new one.

## Remaining O5 gate

The v0.1 format carries only attributed lifecycle receipts. It does not
define issuer federation, authoritative ordering across producers, an event
subscription protocol, or the receiver's pause/review policy. The Proofpress
candidate proposal bridge blocks new proposals from stale receipt snapshots,
withdrawn/rejected origin packages, and unresolved links, but a later foreign
receipt does not yet affect a previously admitted local claim. O5 completes
only when an authenticated receiver can reconcile that later event, record its
local decision, stop affected reuse when warranted, and explain the change in
a real two-system test.
