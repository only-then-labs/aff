"""Workspace-partitioned storage for untrusted OAFF candidate packages.

The caller authenticates and supplies the workspace key. This store never
grants adoption or interprets an originating organization's authority.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Mapping

import rfc8785

from .verify import MAX_PACKAGE_BYTES, verify_bytes


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CandidateInbox:
    def __init__(self, path: str | Path):
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS revisions (
                workspace TEXT NOT NULL,
                finding_id TEXT NOT NULL,
                revision TEXT NOT NULL,
                finding_hash TEXT NOT NULL,
                PRIMARY KEY (workspace, finding_id, revision)
            );
            CREATE TABLE IF NOT EXISTS snapshots (
                workspace TEXT NOT NULL,
                package_digest TEXT NOT NULL,
                finding_id TEXT NOT NULL,
                revision TEXT NOT NULL,
                package_bytes BLOB NOT NULL,
                verification_json TEXT NOT NULL,
                receipt_count INTEGER NOT NULL,
                PRIMARY KEY (workspace, package_digest),
                FOREIGN KEY (workspace, finding_id, revision)
                    REFERENCES revisions (workspace, finding_id, revision)
            );
            CREATE TABLE IF NOT EXISTS quarantine (
                id INTEGER PRIMARY KEY,
                workspace TEXT NOT NULL,
                raw_digest TEXT NOT NULL,
                package_bytes BLOB NOT NULL,
                reason TEXT NOT NULL,
                verification_json TEXT NOT NULL
            );
        """)
        columns = {row[1] for row in self.connection.execute("PRAGMA table_info(snapshots)")}
        if "receipt_count" not in columns:
            # Existing inboxes created before O5 retain their exact package bytes.
            with self.connection:
                self.connection.execute("ALTER TABLE snapshots ADD COLUMN receipt_count INTEGER")
                for rowid, data in self.connection.execute(
                    "SELECT rowid,package_bytes FROM snapshots"
                ):
                    self.connection.execute(
                        "UPDATE snapshots SET receipt_count=? WHERE rowid=?",
                        (len(json.loads(data)["receipts"]), rowid),
                    )

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "CandidateInbox":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def ingest(self, workspace: str, data: bytes,
               evidence: Mapping[str, bytes] | None = None) -> dict:
        """Verify and retain a foreign candidate, or quarantine invalid bytes.

        A second snapshot may append receipts to the same immutable Finding.
        Different Finding bytes under one revision URI are quarantined.
        ``workspace`` is an authenticated caller's partition key, not a
        credential and not derived from the untrusted package.
        """
        if not isinstance(workspace, str) or not workspace.strip():
            raise ValueError("authenticated workspace key is required")
        report = verify_bytes(data, evidence)
        raw_digest = _sha(data)
        if report["status"] == "invalid":
            retained = data if len(data) <= MAX_PACKAGE_BYTES else b""
            return self._quarantine(workspace, retained, raw_digest,
                                    report["diagnostics"][0]["code"], report)

        document = json.loads(data)
        finding = document["finding"]
        finding_hash = _sha(rfc8785.dumps(finding))
        package_digest = document["integrity"]["digest"]
        key = (workspace, finding["id"], finding["revision"])
        new_receipts = {row["id"]: rfc8785.dumps(row) for row in document["receipts"]}
        with self.connection:
            prior = self.connection.execute(
                "SELECT finding_hash FROM revisions WHERE workspace=? AND finding_id=? AND revision=?",
                key,
            ).fetchone()
            if prior and prior[0] != finding_hash:
                return self._quarantine(workspace, data, raw_digest,
                                        "conflicting_revision", report)
            existing = self.connection.execute(
                "SELECT 1 FROM snapshots WHERE workspace=? AND package_digest=?",
                (workspace, package_digest),
            ).fetchone()
            if existing:
                return self._result("idempotent", report, package_digest)
            for (old_bytes,) in self.connection.execute(
                "SELECT package_bytes FROM snapshots WHERE workspace=? AND "
                "finding_id=? AND revision=?", key,
            ):
                old_receipts = {
                    row["id"]: rfc8785.dumps(row)
                    for row in json.loads(old_bytes)["receipts"]
                }
                if any(old_receipts[receipt_id] != new_receipts[receipt_id]
                       for receipt_id in old_receipts.keys() & new_receipts.keys()):
                    return self._quarantine(workspace, data, raw_digest,
                                            "conflicting_receipt_identity", report)
                if not (old_receipts.keys() <= new_receipts.keys()
                        or new_receipts.keys() <= old_receipts.keys()):
                    return self._quarantine(workspace, data, raw_digest,
                                            "divergent_receipt_history", report)
            if not prior:
                self.connection.execute(
                    "INSERT INTO revisions VALUES (?, ?, ?, ?)", (*key, finding_hash)
                )
            self.connection.execute(
                "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
                (workspace, package_digest, finding["id"], finding["revision"],
                 data, json.dumps(report, sort_keys=True), len(new_receipts)),
            )
        return self._result("candidate", report, package_digest)

    def _quarantine(self, workspace: str, data: bytes, raw_digest: str,
                    reason: str, report: dict) -> dict:
        with self.connection:
            self.connection.execute(
                "INSERT INTO quarantine (workspace, raw_digest, package_bytes, reason, verification_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (workspace, raw_digest, data, reason, json.dumps(report, sort_keys=True)),
            )
        return self._result("quarantined", report, raw_digest, reason=reason)

    @staticmethod
    def _result(state: str, report: dict, digest: str, *, reason: str | None = None) -> dict:
        return {
            "state": state,
            "digest": digest,
            "reason": reason,
            "verification": report,
            "local_authority": "none",
        }

    def counts(self, workspace: str) -> dict[str, int]:
        """Return partition-local counts without exposing another workspace."""
        return {
            "revisions": self.connection.execute(
                "SELECT count(*) FROM revisions WHERE workspace=?", (workspace,)
            ).fetchone()[0],
            "snapshots": self.connection.execute(
                "SELECT count(*) FROM snapshots WHERE workspace=?", (workspace,)
            ).fetchone()[0],
            "quarantined": self.connection.execute(
                "SELECT count(*) FROM quarantine WHERE workspace=?", (workspace,)
            ).fetchone()[0],
        }

    def list_candidates(self, workspace: str, *, limit: int = 20,
                        before: str | None = None) -> list[dict]:
        """Summarize the latest retained snapshot of each immutable revision.

        This is an untrusted review queue, never a list of adopted knowledge.
        Later receipt snapshots replace the displayed snapshot, not history.
        """
        if not isinstance(workspace, str) or not workspace.strip():
            raise ValueError("authenticated workspace key is required")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        before_rowid = None
        if before is not None:
            if not isinstance(before, str) or not before:
                raise ValueError("before must be a retained package digest")
            row = self.connection.execute(
                "SELECT rowid FROM snapshots WHERE workspace=? AND package_digest=?",
                (workspace, before),
            ).fetchone()
            if row is None:
                raise ValueError("before cursor is not retained in this workspace")
            before_rowid = row[0]
        rows = self.connection.execute(
            "SELECT s.package_digest,s.finding_id,s.revision,s.package_bytes,"
            "s.verification_json FROM snapshots s WHERE s.workspace=? AND "
            "(? IS NULL OR s.rowid < ?) AND "
            "s.rowid=(SELECT newer.rowid FROM snapshots newer WHERE "
            "newer.workspace=s.workspace AND newer.finding_id=s.finding_id "
            "AND newer.revision=s.revision ORDER BY newer.receipt_count DESC, "
            "newer.rowid DESC LIMIT 1) ORDER BY s.rowid DESC LIMIT ?",
            (workspace, before_rowid, before_rowid, limit),
        ).fetchall()
        summaries = []
        for digest, finding_id, revision, package_bytes, verification_json in rows:
            finding = json.loads(package_bytes)["finding"]
            summaries.append({
                "digest": digest, "finding_id": finding_id, "revision": revision,
                "statement": finding["statement"], "type": finding["type"],
                "applicability": finding["applicability"],
                "producer": finding["producer"],
                "evidence_count": len(finding["evidence"]),
                "verification": json.loads(verification_json),
                "local_authority": "none",
            })
        return summaries

    def get_candidate(self, workspace: str, package_digest: str) -> dict | None:
        """Return one workspace-local retained snapshot for explicit review."""
        if not isinstance(workspace, str) or not workspace.strip():
            raise ValueError("authenticated workspace key is required")
        if not isinstance(package_digest, str) or not package_digest:
            raise ValueError("package digest is required")
        row = self.connection.execute(
            "SELECT rowid,finding_id,revision,package_bytes,verification_json FROM snapshots "
            "WHERE workspace=? AND package_digest=?",
            (workspace, package_digest),
        ).fetchone()
        if row is None:
            return None
        latest_rowid = self.connection.execute(
            "SELECT rowid FROM snapshots WHERE workspace=? AND "
            "finding_id=? AND revision=? ORDER BY receipt_count DESC,rowid DESC LIMIT 1",
            (workspace, row[1], row[2]),
        ).fetchone()[0]
        return {"digest": package_digest, "package": json.loads(row[3]),
                "verification": json.loads(row[4]),
                "latest_snapshot": row[0] == latest_rowid,
                "local_authority": "none"}

    def lineage(self, workspace: str, finding_id: str) -> dict | None:
        """Show retained revision and lifecycle claims for local review.

        Ingestion order chooses the displayed receipt snapshot *within* each
        immutable revision. It cannot establish the current revision, issuer
        authenticity, or a receiver-side withdrawal decision.
        """
        if not isinstance(workspace, str) or not workspace.strip():
            raise ValueError("authenticated workspace key is required")
        if not isinstance(finding_id, str) or not finding_id:
            raise ValueError("finding ID is required")
        total = self.connection.execute(
            "SELECT count(*) FROM revisions WHERE workspace=? AND finding_id=?",
            (workspace, finding_id),
        ).fetchone()[0]
        if not total:
            return None
        rows = self.connection.execute(
            "SELECT s.package_digest,s.revision,s.package_bytes,count(older.rowid) "
            "FROM snapshots s JOIN snapshots older ON older.workspace=s.workspace "
            "AND older.finding_id=s.finding_id AND older.revision=s.revision "
            "WHERE s.workspace=? AND s.finding_id=? AND s.rowid=(SELECT newer.rowid "
            "FROM snapshots newer WHERE newer.workspace=s.workspace AND "
            "newer.finding_id=s.finding_id AND newer.revision=s.revision "
            "ORDER BY newer.receipt_count DESC,newer.rowid DESC LIMIT 1) "
            "GROUP BY s.rowid ORDER BY s.rowid DESC LIMIT 100",
            (workspace, finding_id),
        ).fetchall()
        retained = {
            (row[0], row[1])
            for row in self.connection.execute(
                "SELECT finding_id,revision FROM revisions WHERE workspace=?", (workspace,)
            )
        }
        revisions = []
        for digest, revision, package_bytes, snapshot_count in rows:
            package = json.loads(package_bytes)
            links = []
            for link in package["finding"].get("links", []):
                links.append({**link, "target_retained":
                              (link["target_id"], link["target_revision"]) in retained})
            revisions.append({
                "revision": revision,
                "package_digest": digest,
                "snapshot_count": snapshot_count,
                "created_at_claimed": package["finding"]["created_at"],
                "links_claimed": links,
                "origin_decisions_claimed": [
                    {"kind": receipt["kind"], "result": receipt["result"],
                     "issuer": receipt["issuer"], "issued_at": receipt["issued_at"]}
                    for receipt in package["receipts"]
                    if receipt["kind"] in {"adoption_decision", "lifecycle"}
                ],
            })
        return {"finding_id": finding_id, "revisions": revisions,
                "total_revisions": total, "has_more": total > len(revisions),
                "current_revision": "undetermined",
                "local_review_required": True, "local_authority": "none"}
