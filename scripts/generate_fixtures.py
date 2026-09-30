#!/usr/bin/env python3
"""Regenerate synthetic O1 fixtures; examples are not real-world evidence."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import rfc8785


ROOT = Path(__file__).resolve().parents[1] / "fixtures"
FINDING_ID = "tag:example.org,2026:oaff/finding/retry-42"
REVISION_1 = "tag:example.org,2026:oaff/revision/retry-42-v1"
REVISION_2 = "tag:example.org,2026:oaff/revision/retry-42-v2"
SOURCE_DIGEST = hashlib.sha256(b"synthetic run 42: retry with the same key").hexdigest()


def write(name: str, value: dict, *, seal: bool = True) -> None:
    if seal:
        unsigned = {key: item for key, item in value.items() if key != "integrity"}
        value["integrity"] = {
            "algorithm": "sha-256-jcs",
            "digest": hashlib.sha256(rfc8785.dumps(unsigned)).hexdigest(),
        }
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


base = {
    "oaff_version": "0.1.0",
    "finding": {
        "id": FINDING_ID,
        "revision": REVISION_1,
        "statement": "In the synthetic API v2 run, retrying create with the same idempotency key did not create a duplicate.",
        "type": "observation",
        "applicability": {
            "description": "Synthetic API create calls after an ambiguous timeout.",
            "conditions": ["API v2", "The retry uses the identical idempotency key."],
            "exclusions": ["No idempotency key was supplied."],
        },
        "producer": {"id": "tag:example.org,2026:agent/researcher", "kind": "agent"},
        "created_at": "2026-09-29T12:00:00Z",
        "evidence": [
            {
                "id": "run-42",
                "source_uri": "https://example.org/runs/42",
                "content_digest": {"algorithm": "sha-256", "value": SOURCE_DIGEST},
                "availability": "restricted",
                "locator": "attempt 2 / result",
                "excerpt": "Synthetic example: one resource identifier observed after retry.",
            }
        ],
    },
    "receipts": [],
}

write("valid/candidate-valid.aff", copy.deepcopy(base))

admitted = copy.deepcopy(base)
admitted["receipts"] = [
    {
        "id": "tag:example.org,2026:oaff/receipt/support-42",
        "kind": "support_assessment",
        "subject_revision": REVISION_1,
        "issuer": {"id": "tag:example.org,2026:agent/reviewer", "kind": "agent"},
        "issued_at": "2026-09-29T12:10:00Z",
        "method": "synthetic-fixture-review/v1",
        "result": "indeterminate",
        "evidence_refs": ["run-42"],
        "explanation": "The source is restricted; the receiver cannot inspect it from this package.",
    },
    {
        "id": "tag:example.org,2026:oaff/receipt/decision-42",
        "kind": "adoption_decision",
        "subject_revision": REVISION_1,
        "issuer": {"id": "tag:example.org,2026:human/owner", "kind": "human"},
        "issued_at": "2026-09-29T12:20:00Z",
        "method": "synthetic-origin-review/v1",
        "result": "admitted",
        "authority_basis": "human_approval",
        "evidence_refs": ["run-42"],
        "explanation": "Illustrative origin decision only; this is not authenticated evidence.",
    },
]
write("valid/admitted-valid.aff", admitted)

withdrawn = copy.deepcopy(admitted)
withdrawn["receipts"].append(
    {
        "id": "tag:example.org,2026:oaff/receipt/withdrawal-42",
        "kind": "lifecycle",
        "subject_revision": REVISION_1,
        "issuer": {"id": "tag:example.org,2026:human/owner", "kind": "human"},
        "issued_at": "2026-09-30T09:00:00Z",
        "method": "synthetic-origin-withdrawal/v1",
        "result": "withdrawn",
        "explanation": "Illustrative withdrawal; external authority is not authenticated.",
    }
)
write("valid/withdrawn-valid.aff", withdrawn)

revision = copy.deepcopy(base)
revision["finding"]["revision"] = REVISION_2
revision["finding"]["statement"] = (
    "In the synthetic API v2 run, retrying create with the same idempotency key "
    "returned the original resource identifier."
)
revision["finding"]["links"] = [
    {"relation": "revision_of", "target_id": FINDING_ID, "target_revision": REVISION_1}
]
write("valid/revision-valid.aff", revision)

conflicting = copy.deepcopy(base)
conflicting["finding"]["id"] = "tag:example.org,2026:oaff/finding/conflict-1"
conflicting["finding"]["revision"] = "tag:example.org,2026:oaff/revision/conflict-1"
conflicting["finding"]["statement"] = "The synthetic API returns the original resource identifier on retry."
conflicting["finding"]["evidence"].append(
    {
        "id": "run-43",
        "source_uri": "https://example.org/runs/43",
        "content_digest": {
            "algorithm": "sha-256",
            "value": hashlib.sha256(b"synthetic run 43: new resource").hexdigest(),
        },
        "availability": "restricted",
        "excerpt": "Synthetic counterexample: a new resource identifier was observed.",
    }
)
conflicting["receipts"] = [
    {
        "id": "tag:example.org,2026:oaff/receipt/conflict-check",
        "kind": "support_assessment",
        "subject_revision": conflicting["finding"]["revision"],
        "issuer": {"id": "tag:example.org,2026:agent/reviewer", "kind": "agent"},
        "issued_at": "2026-09-29T13:00:00Z",
        "method": "synthetic-conflict-screen/v1",
        "result": "indeterminate",
        "evidence_refs": ["run-42", "run-43"],
    }
]
write("valid/conflicting-evidence-valid.aff", conflicting)

unavailable = copy.deepcopy(base)
unavailable["finding"]["id"] = "tag:example.org,2026:oaff/finding/unavailable-1"
unavailable["finding"]["revision"] = "tag:example.org,2026:oaff/revision/unavailable-1"
unavailable["finding"]["evidence"][0]["availability"] = "unavailable"
write("valid/unavailable-evidence-valid.aff", unavailable)

# A run is evidence; the reusable conclusion is the Finding. These two
# packages deliberately use the same v0.1 shape for positive and negative
# observations. The tiny source files allow a verifier to check exact bytes.
run_cases = [
    (
        "successful",
        b"synthetic run success-1: timeout; retry with key K; original resource id returned\n",
        "After an ambiguous timeout, retrying create with the same idempotency key returned the original resource in this synthetic API v2 run.",
        "A create call timed out ambiguously and the retry used the same key.",
        ["API v2", "The retry used the original idempotency key."],
        ["The initial create outcome was known before retry."],
    ),
    (
        "failed",
        b"synthetic run failure-1: timeout; retry with new key K2; second resource id returned\n",
        "After an ambiguous timeout, retrying create with a new idempotency key created a second resource in this synthetic API v2 run.",
        "A create call timed out ambiguously and the retry changed the key.",
        ["API v2", "The retry used a new idempotency key."],
        ["The retry used the original idempotency key."],
    ),
]
for outcome, source_bytes, statement, description, conditions, exclusions in run_cases:
    source_path = ROOT / "sources" / f"{outcome}-run.txt"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes(source_bytes)
    package = copy.deepcopy(base)
    package["finding"].update(
        {
            "id": f"tag:example.org,2026:oaff/finding/{outcome}-run-1",
            "revision": f"tag:example.org,2026:oaff/revision/{outcome}-run-1-v1",
            "statement": statement,
            "applicability": {
                "description": description,
                "conditions": conditions,
                "exclusions": exclusions,
            },
            "evidence": [
                {
                    "id": f"run-{outcome}-1",
                    "source_uri": f"https://example.org/synthetic/runs/{outcome}-1",
                    "content_digest": {
                        "algorithm": "sha-256",
                        "value": hashlib.sha256(source_bytes).hexdigest(),
                    },
                    "availability": "restricted",
                    "locator": "result summary",
                    "excerpt": source_bytes.decode("utf-8").strip(),
                }
            ],
        }
    )
    write(f"valid/{outcome}-run-finding-valid.aff", package)

missing_scope = copy.deepcopy(base)
del missing_scope["finding"]["applicability"]
write("invalid/missing-applicability.aff", missing_scope)

wrong_result = copy.deepcopy(admitted)
wrong_result["receipts"][0]["result"] = "admitted"
write("invalid/wrong-receipt-result.aff", wrong_result)

tampered = copy.deepcopy(base)
write("invalid/tampered-statement.aff", tampered)
path = ROOT / "invalid/tampered-statement.aff"
path.write_text(path.read_text().replace("did not create a duplicate", "created a duplicate"))

wrong_subject = copy.deepcopy(admitted)
wrong_subject["receipts"][0]["subject_revision"] = REVISION_2
write("invalid/wrong-subject.aff", wrong_subject)

unknown_evidence = copy.deepcopy(admitted)
unknown_evidence["receipts"][0]["evidence_refs"] = ["not-present"]
write("invalid/unknown-evidence.aff", unknown_evidence)

self_revision = copy.deepcopy(revision)
self_revision["finding"]["links"][0]["target_revision"] = REVISION_2
write("invalid/self-revision.aff", self_revision)

(ROOT / "invalid/duplicate-key.aff").write_text(
    '{"oaff_version":"0.1.0","oaff_version":"0.1.0"}\n'
)
print("Generated 15 synthetic fixture files and two synthetic source files")
