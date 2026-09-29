#!/usr/bin/env python3
"""Check O1's example contract; O2 will provide the standalone verifier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema
import rfc8785


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schema/oaff-0.1.schema.json").read_text())
MANIFEST = json.loads((ROOT / "fixtures/manifest.json").read_text())
VALIDATOR = jsonschema.Draft202012Validator(
    SCHEMA, format_checker=jsonschema.FormatChecker()
)


class FixtureError(Exception):
    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def reject_constant(value: str) -> object:
    raise ValueError(f"non-JSON constant: {value}")


def check(path: Path) -> None:
    try:
        doc = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=no_duplicate_keys,
            parse_constant=reject_constant,
        )
        rfc8785.dumps(doc)
    except (ValueError, UnicodeError, rfc8785.CanonicalizationError) as error:
        raise FixtureError("invalid_json", str(error)) from error

    errors = sorted(VALIDATOR.iter_errors(doc), key=lambda error: str(error.path))
    if errors:
        raise FixtureError("invalid_schema", errors[0].message)

    finding = doc["finding"]
    evidence_ids = [item["id"] for item in finding["evidence"]]
    if len(set(evidence_ids)) != len(evidence_ids):
        raise FixtureError("invalid_binding", "duplicate evidence ID")
    receipt_ids = [item["id"] for item in doc["receipts"]]
    if len(set(receipt_ids)) != len(receipt_ids):
        raise FixtureError("invalid_binding", "duplicate receipt ID")
    for receipt in doc["receipts"]:
        if receipt["subject_revision"] != finding["revision"]:
            raise FixtureError("invalid_binding", "wrong receipt subject")
        if not set(receipt.get("evidence_refs", [])).issubset(evidence_ids):
            raise FixtureError("invalid_binding", "unknown receipt evidence")
    for link in finding.get("links", []):
        if link["relation"] == "revision_of":
            if link["target_id"] != finding["id"]:
                raise FixtureError("invalid_binding", "revision_of changes Finding ID")
            if link["target_revision"] == finding["revision"]:
                raise FixtureError("invalid_binding", "self revision")

    unsigned = {key: value for key, value in doc.items() if key != "integrity"}
    actual = hashlib.sha256(rfc8785.dumps(unsigned)).hexdigest()
    if actual != doc["integrity"]["digest"]:
        raise FixtureError("invalid_binding", "package digest mismatch")


def main() -> None:
    jsonschema.Draft202012Validator.check_schema(SCHEMA)
    count = 0
    for relative in MANIFEST["valid"]:
        path = ROOT / "fixtures" / relative
        check(path)
        print(f"PASS valid   {relative}")
        count += 1
    for relative, expected in MANIFEST["invalid"].items():
        path = ROOT / "fixtures" / relative
        try:
            check(path)
        except FixtureError as error:
            if error.category != expected:
                raise AssertionError(
                    f"{relative}: expected {expected}, got {error.category}: {error}"
                ) from error
            print(f"PASS {expected:15} {relative}")
        else:
            raise AssertionError(f"{relative}: unexpectedly valid")
        count += 1
    listed = {
        str(path.relative_to(ROOT / "fixtures"))
        for path in (ROOT / "fixtures").rglob("*.oaff.json")
    }
    expected_files = set(MANIFEST["valid"]) | set(MANIFEST["invalid"])
    if listed != expected_files:
        raise AssertionError(
            f"manifest mismatch; unlisted={listed - expected_files}, missing={expected_files - listed}"
        )
    print(f"{count} fixture cases passed")


if __name__ == "__main__":
    main()
