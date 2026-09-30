import copy
import hashlib
import json
import sqlite3
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
            self.assertTrue(selected["latest_snapshot"])
            self.assertFalse(inbox.get_candidate("workspace-a", original["digest"])[
                "latest_snapshot"])
            self.assertEqual(selected["local_authority"], "none")
            with self.assertRaisesRegex(ValueError, "limit"):
                inbox.list_candidates("workspace-a", limit=101)

    def test_candidate_pages_use_workspace_local_digest_cursor(self):
        files = ("candidate-valid", "revision-valid", "failed-run-finding-valid")
        with TemporaryDirectory() as directory, CandidateInbox(Path(directory) / "inbox.db") as inbox:
            for name in files:
                inbox.ingest("workspace-a", (FIXTURES / f"valid/{name}.oaff.json").read_bytes())
            inbox.ingest("workspace-b", (FIXTURES / "valid/candidate-valid.oaff.json").read_bytes())
            seen = []
            cursor = None
            while page := inbox.list_candidates("workspace-a", limit=1, before=cursor):
                seen.append(page[0]["revision"])
                cursor = page[-1]["digest"]
            self.assertEqual(len(seen), 3)
            self.assertEqual(len(set(seen)), 3)
            foreign_only = inbox.list_candidates("workspace-a", limit=1)[0]["digest"]
            with self.assertRaisesRegex(ValueError, "cursor"):
                inbox.list_candidates("workspace-b", before=foreign_only)

    def test_lineage_inspection_keeps_origin_lifecycle_untrusted(self):
        finding_id = "tag:example.org,2026:oaff/finding/retry-42"
        with TemporaryDirectory() as directory, CandidateInbox(
            Path(directory) / "inbox.db"
        ) as inbox:
            for name in ("candidate-valid", "admitted-valid", "withdrawn-valid",
                         "revision-valid"):
                inbox.ingest("workspace-a", (FIXTURES / f"valid/{name}.oaff.json").read_bytes())
            inbox.ingest("workspace-b", (FIXTURES / "valid/candidate-valid.oaff.json").read_bytes())
            lineage = inbox.lineage("workspace-a", finding_id)
            self.assertEqual(lineage["total_revisions"], 2)
            self.assertEqual(lineage["current_revision"], "undetermined")
            self.assertTrue(lineage["local_review_required"])
            self.assertEqual(lineage["local_authority"], "none")
            newer, earlier = lineage["revisions"]
            self.assertEqual(newer["links_claimed"][0]["relation"], "revision_of")
            self.assertTrue(newer["links_claimed"][0]["target_retained"])
            self.assertEqual(earlier["snapshot_count"], 3)
            self.assertIn("withdrawn", [row["result"] for row in
                         earlier["origin_decisions_claimed"]])
            other = inbox.lineage("workspace-b", finding_id)
            self.assertEqual(other["total_revisions"], 1)
            self.assertEqual(other["revisions"][0]["origin_decisions_claimed"], [])
            self.assertIsNone(inbox.lineage("workspace-b", "tag:example.org,2026:missing"))

    def test_out_of_order_snapshot_cannot_hide_withdrawal(self):
        candidate = (FIXTURES / "valid/candidate-valid.oaff.json").read_bytes()
        admitted = (FIXTURES / "valid/admitted-valid.oaff.json").read_bytes()
        withdrawn = (FIXTURES / "valid/withdrawn-valid.oaff.json").read_bytes()
        with TemporaryDirectory() as directory, CandidateInbox(Path(directory) / "inbox.db") as inbox:
            latest = inbox.ingest("workspace-a", withdrawn)
            inbox.ingest("workspace-a", candidate)
            inbox.ingest("workspace-a", admitted)
            self.assertEqual(inbox.list_candidates("workspace-a")[0]["digest"],
                             latest["digest"])
            self.assertTrue(inbox.get_candidate("workspace-a", latest["digest"])[
                "latest_snapshot"])
            finding_id = json.loads(candidate)["finding"]["id"]
            self.assertEqual(inbox.lineage("workspace-a", finding_id)["revisions"][0][
                "snapshot_count"], 3)

    def test_divergent_or_mutated_receipt_history_is_quarantined(self):
        admitted = json.loads((FIXTURES / "valid/admitted-valid.oaff.json").read_bytes())
        changed = copy.deepcopy(admitted)
        changed["receipts"][0]["result"] = "supported"
        branch = copy.deepcopy(admitted)
        branch["receipts"] = [branch["receipts"][0]]
        branch["receipts"].append({
            "id": "tag:example.org,2026:oaff/receipt/other",
            "kind": "lifecycle", "subject_revision": branch["finding"]["revision"],
            "issuer": {"id": "tag:example.org,2026:human/other", "kind": "human"},
            "issued_at": "2026-09-30T12:00:00Z", "method": "synthetic",
            "result": "withdrawn",
        })
        with TemporaryDirectory() as directory, CandidateInbox(Path(directory) / "inbox.db") as inbox:
            inbox.ingest("workspace-a", seal(admitted))
            self.assertEqual(inbox.ingest("workspace-a", seal(changed))["reason"],
                             "conflicting_receipt_identity")
            self.assertEqual(inbox.ingest("workspace-a", seal(branch))["reason"],
                             "divergent_receipt_history")
            self.assertEqual(inbox.counts("workspace-a")["snapshots"], 1)

    def test_existing_inbox_receipt_counts_are_migrated(self):
        admitted = (FIXTURES / "valid/admitted-valid.oaff.json").read_bytes()
        package = json.loads(admitted)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "old.db"
            connection = sqlite3.connect(path)
            connection.executescript("""
                CREATE TABLE revisions(workspace TEXT, finding_id TEXT,
                    revision TEXT, finding_hash TEXT,
                    PRIMARY KEY(workspace,finding_id,revision));
                CREATE TABLE snapshots(workspace TEXT, package_digest TEXT,
                    finding_id TEXT, revision TEXT, package_bytes BLOB,
                    verification_json TEXT,
                    PRIMARY KEY(workspace,package_digest));
            """)
            finding = package["finding"]
            connection.execute("INSERT INTO revisions VALUES (?,?,?,?)", (
                "workspace-a", finding["id"], finding["revision"],
                hashlib.sha256(rfc8785.dumps(finding)).hexdigest()))
            connection.execute("INSERT INTO snapshots VALUES (?,?,?,?,?,?)", (
                "workspace-a", package["integrity"]["digest"], finding["id"],
                finding["revision"], admitted, "{}"))
            connection.commit()
            connection.close()
            with CandidateInbox(path) as inbox:
                count = inbox.connection.execute(
                    "SELECT receipt_count FROM snapshots"
                ).fetchone()[0]
                self.assertEqual(count, len(package["receipts"]))
                self.assertTrue(inbox.get_candidate(
                    "workspace-a", package["integrity"]["digest"])["latest_snapshot"])

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
