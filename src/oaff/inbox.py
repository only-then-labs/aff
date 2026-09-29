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

from .verify import verify_bytes


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
            return self._quarantine(workspace, data, raw_digest,
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
