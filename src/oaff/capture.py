"""Create an AFF Finding from a local source and explicit human-supplied fields."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import rfc8785

from .verify import verify_bytes


class CaptureError(ValueError):
    """The requested Finding cannot be created safely."""


def capture_source(
    *,
    source: Path,
    source_uri: str,
    output: Path,
    statement: str,
    applicability: str,
    conditions: list[str],
    producer_id: str,
    producer_kind: str,
    finding_type: str = "observation",
    exclusions: list[str] | None = None,
    availability: str = "restricted",
    locator: str | None = None,
) -> Path:
    """Bind a new Finding to exact source bytes without copying source content.

    This records a proposed observation, not verified support or local adoption.
    IDs are generated for a new Finding and its first immutable revision.
    """

    if source.is_symlink() or not source.is_file():
        raise CaptureError("source must be a regular file, not a symlink")
    digest = hashlib.sha256()
    try:
        with source.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise CaptureError(f"cannot read source: {exc}") from exc

    evidence = {
        "id": "source-1",
        "source_uri": source_uri,
        "content_digest": {"algorithm": "sha-256", "value": digest.hexdigest()},
        "availability": availability,
    }
    if locator is not None:
        evidence["locator"] = locator
    scope = {"description": applicability, "conditions": conditions}
    if exclusions:
        scope["exclusions"] = exclusions
    document = {
        "oaff_version": "0.1.0",
        "finding": {
            "id": f"urn:uuid:{uuid4()}",
            "revision": f"urn:uuid:{uuid4()}",
            "statement": statement,
            "type": finding_type,
            "applicability": scope,
            "producer": {"id": producer_id, "kind": producer_kind},
            "created_at": datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
            "evidence": [evidence],
        },
        "receipts": [],
    }
    document["integrity"] = {
        "algorithm": "sha-256-jcs",
        "digest": hashlib.sha256(rfc8785.dumps(document)).hexdigest(),
    }
    encoded = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8"
    )
    result = verify_bytes(encoded)
    if result["status"] == "invalid":
        details = "; ".join(item["message"] for item in result["diagnostics"])
        raise CaptureError(f"invalid Finding fields: {details}")
    try:
        with output.open("xb") as stream:
            stream.write(encoded)
    except FileExistsError as exc:
        raise CaptureError(f"output already exists: {output}") from exc
    except OSError as exc:
        raise CaptureError(f"cannot write output: {exc}") from exc
    return output
