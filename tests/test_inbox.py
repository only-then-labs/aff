import copy
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import rfc8785

from oaff.inbox import CandidateInbox


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def seal(document: dict) -> bytes:
    document["integrity"]["digest"] = hashlib.sha256(
        rfc8785.dumps({key: value for key, value in document.items() if key != "integrity"})
    ).hexdigest()
    return json.dumps(document).encode()


class InboxTests(unittest.TestCase):
    def test_idempotent_receipt_snapshots_and_workspace_partition(self):
        candidate = (FIXTURES / "valid/candidate-valid.oaff.json").read_bytes()
        admitted = (FIXTURES / "valid/admitted-valid.oaff.json").read_bytes()
        with TemporaryDirectory() as directory, CandidateInbox(Path(directory) / "inbox.db") as inbox:
            first = inbox.ingest("workspace-a", candidate)
            self.assertEqual(first["state"], "candidate")
            self.assertEqual(first["local_authority"], "none")
            self.assertEqual(inbox.ingest("workspace-a", candidate)["state"], "idempotent")
            self.assertEqual(inbox.ingest("workspace-a", admitted)["state"], "candidate")
            self.assertEqual(inbox.counts("workspace-a"),
                             {"revisions": 1, "snapshots": 2, "quarantined": 0})
            self.assertEqual(inbox.counts("workspace-b"),
                             {"revisions": 0, "snapshots": 0, "quarantined": 0})
            self.assertEqual(inbox.ingest("workspace-b", admitted)["state"], "candidate")

    def test_conflicting_identity_is_quarantined_even_with_new_valid_digest(self):
        candidate = (FIXTURES / "valid/candidate-valid.oaff.json").read_bytes()
        changed = copy.deepcopy(json.loads(candidate))
        changed["finding"]["statement"] = "Different claim under the same revision."
        conflict = seal(changed)
        with TemporaryDirectory() as directory, CandidateInbox(Path(directory) / "inbox.db") as inbox:
            inbox.ingest("workspace-a", candidate)
            result = inbox.ingest("workspace-a", conflict)
            self.assertEqual(result["state"], "quarantined")
            self.assertEqual(result["reason"], "conflicting_revision")
            self.assertEqual(inbox.counts("workspace-a"),
                             {"revisions": 1, "snapshots": 1, "quarantined": 1})

    def test_inspection_uses_latest_snapshot_and_never_crosses_workspace(self):
        candidate = (FIXTURES / "valid/candidate-valid.oaff.json").read_bytes()
        admitted = (FIXTURES / "valid/admitted-valid.oaff.json").read_bytes()
        with TemporaryDirectory() as directory, CandidateInbox(Path(directory) / "inbox.db") as inbox:
            original = inbox.ingest("workspace-a", candidate)
            latest = inbox.ingest("workspace-a", admitted)
            inbox.ingest("workspace-b", candidate)
            rows = inbox.list_candidates("workspace-a")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["digest"], latest["digest"])
            self.assertEqual(rows[0]["local_authority"], "none")
            self.assertEqual(rows[0]["verification"]["receipt_counts"]["adoption_decision"], 1)
            self.assertEqual(inbox.list_candidates("workspace-b")[0]["digest"],
                             original["digest"])
            self.assertIsNone(inbox.get_candidate("workspace-b", latest["digest"]))
            selected = inbox.get_candidate("workspace-a", latest["digest"])
            self.assertEqual(selected["package"]["receipts"][-1]["result"], "admitted")
            self.assertEqual(selected["local_authority"], "none")
            with self.assertRaisesRegex(ValueError, "limit"):
                inbox.list_candidates("workspace-a", limit=101)

    def test_tampered_and_mismatched_evidence_are_quarantined(self):
        candidate = (FIXTURES / "valid/candidate-valid.oaff.json").read_bytes()
        tampered = (FIXTURES / "invalid/tampered-statement.oaff.json").read_bytes()
        with TemporaryDirectory() as directory, CandidateInbox(Path(directory) / "inbox.db") as inbox:
            self.assertEqual(inbox.ingest("workspace-a", tampered)["reason"], "invalid_binding")
            self.assertEqual(inbox.ingest("workspace-a", candidate,
                                          {"run-42": b"wrong"})["reason"], "evidence_mismatch")
            self.assertEqual(inbox.counts("workspace-a")["snapshots"], 0)
            self.assertEqual(inbox.counts("workspace-a")["quarantined"], 2)

    def test_empty_workspace_is_rejected(self):
        candidate = (FIXTURES / "valid/candidate-valid.oaff.json").read_bytes()
        with TemporaryDirectory() as directory, CandidateInbox(Path(directory) / "inbox.db") as inbox:
            with self.assertRaisesRegex(ValueError, "workspace key"):
                inbox.ingest("", candidate)

    def test_oversized_package_is_rejected_without_storing_its_bytes(self):
        from oaff.verify import MAX_PACKAGE_BYTES
        oversized = b"x" * (MAX_PACKAGE_BYTES + 1)
        with TemporaryDirectory() as directory, CandidateInbox(Path(directory) / "inbox.db") as inbox:
            result = inbox.ingest("workspace-a", oversized)
            self.assertEqual(result["state"], "quarantined")
            length = inbox.connection.execute(
                "SELECT length(package_bytes) FROM quarantine"
            ).fetchone()[0]
            self.assertEqual(length, 0)


if __name__ == "__main__":
    unittest.main()
