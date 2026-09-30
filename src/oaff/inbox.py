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
            if not prior:
                self.connection.execute(
                    "INSERT INTO revisions VALUES (?, ?, ?, ?)", (*key, finding_hash)
                )
            self.connection.execute(
                "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?)",
                (workspace, package_digest, finding["id"], finding["revision"],
                 data, json.dumps(report, sort_keys=True)),
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

    def list_candidates(self, workspace: str, *, limit: int = 20) -> list[dict]:
        """Summarize the latest retained snapshot of each immutable revision.

        This is an untrusted review queue, never a list of adopted knowledge.
        Later receipt snapshots replace the displayed snapshot, not history.
        """
        if not isinstance(workspace, str) or not workspace.strip():
            raise ValueError("authenticated workspace key is required")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        rows = self.connection.execute(
            "SELECT s.package_digest,s.finding_id,s.revision,s.package_bytes,"
            "s.verification_json FROM snapshots s WHERE s.workspace=? AND "
            "s.rowid=(SELECT max(newer.rowid) FROM snapshots newer WHERE "
            "newer.workspace=s.workspace AND newer.finding_id=s.finding_id "
            "AND newer.revision=s.revision) ORDER BY s.rowid DESC LIMIT ?",
            (workspace, limit),
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
            "SELECT max(rowid) FROM snapshots WHERE workspace=? AND "
            "finding_id=? AND revision=?",
            (workspace, row[1], row[2]),
        ).fetchone()[0]
        return {"digest": package_digest, "package": json.loads(row[3]),
                "verification": json.loads(row[4]),
                "latest_snapshot": row[0] == latest_rowid,
                "local_authority": "none"}
