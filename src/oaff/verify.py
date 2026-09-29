"""Validate OAFF packages without fetching URIs or granting local authority."""

from __future__ import annotations

import hashlib
import json
from importlib import resources
from pathlib import Path
from typing import Mapping

import jsonschema
import rfc8785

MAX_PACKAGE_BYTES = 10 * 1024 * 1024


def _schema() -> dict:
    resource = resources.files("oaff").joinpath("schema.json")
    if resource.is_file():
        return json.loads(resource.read_text(encoding="utf-8"))
    # Editable checkouts keep the single normative schema at the repo root.
    checkout_schema = Path(__file__).resolve().parents[2] / "schema/oaff-0.1.schema.json"
    return json.loads(checkout_schema.read_text(encoding="utf-8"))


_VALIDATOR = jsonschema.Draft202012Validator(
    _schema(), format_checker=jsonschema.FormatChecker()
)


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON property: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-JSON constant: {value}")


def _result(status: str, *, code: str | None = None, message: str | None = None) -> dict:
    return {
        "status": status,
        "integrity": "not_checked",
        "finding_id": None,
        "revision": None,
        "evidence": [],
        "receipt_counts": {},
        "local_authority": "not_evaluated",
        "diagnostics": [{"code": code, "message": message}] if code else [],
    }


def verify_bytes(data: bytes, evidence: Mapping[str, bytes] | None = None) -> dict:
    """Verify one package and optional caller-supplied source bytes.

    This never authenticates receipt issuers or authorizes adoption. Source
    URIs are never fetched. Uninspected evidence gives valid_with_limits.
    """

    if len(data) > MAX_PACKAGE_BYTES:
        return _result("invalid", code="invalid_json", message="package exceeds 10 MiB")
    try:
        document = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        rfc8785.dumps(document)
    except (UnicodeError, ValueError, TypeError, rfc8785.CanonicalizationError) as exc:
        return _result("invalid", code="invalid_json", message=str(exc))

    errors = sorted(
        _VALIDATOR.iter_errors(document),
        key=lambda item: (list(map(str, item.absolute_path)), item.message),
    )
    if errors:
        error = errors[0]
        path = "/" + "/".join(map(str, error.absolute_path))
        return _result(
            "invalid", code="invalid_schema", message=f"{path}: {error.message}"
        )

    finding = document["finding"]
    report = _result("valid")
    report["finding_id"] = finding["id"]
    report["revision"] = finding["revision"]

    def invalid(message: str, code: str = "invalid_binding") -> dict:
        report["status"] = "invalid"
        report["diagnostics"].append({"code": code, "message": message})
        return report

    evidence_ids = [item["id"] for item in finding["evidence"]]
    if len(evidence_ids) != len(set(evidence_ids)):
        return invalid("duplicate evidence ID")
    receipt_ids = [item["id"] for item in document["receipts"]]
    if len(receipt_ids) != len(set(receipt_ids)):
        return invalid("duplicate receipt ID")
    for receipt in document["receipts"]:
        if receipt["subject_revision"] != finding["revision"]:
            return invalid(f"receipt {receipt['id']} targets a different revision")
        unknown = set(receipt.get("evidence_refs", [])) - set(evidence_ids)
        if unknown:
            return invalid(f"receipt {receipt['id']} cites unknown evidence: {sorted(unknown)}")
    for link in finding.get("links", []):
        if link["relation"] == "revision_of":
            if link["target_id"] != finding["id"]:
                return invalid("revision_of changes the Finding ID")
            if link["target_revision"] == finding["revision"]:
                return invalid("revision_of points to itself")

    unsigned = {key: value for key, value in document.items() if key != "integrity"}
    actual = hashlib.sha256(rfc8785.dumps(unsigned)).hexdigest()
    if actual != document["integrity"]["digest"]:
        report["integrity"] = "fail"
        return invalid("package digest mismatch")
    report["integrity"] = "pass"

    provided = evidence or {}
    unknown_provided = set(provided) - set(evidence_ids)
    if unknown_provided:
        return invalid(f"source bytes supplied for unknown evidence: {sorted(unknown_provided)}")
    limited = False
    for item in finding["evidence"]:
        source = provided.get(item["id"])
        if source is None:
            state = "not_provided"
            limited = True
        elif hashlib.sha256(source).hexdigest() != item["content_digest"]["value"]:
            state = "mismatch"
        else:
            state = "pass"
        report["evidence"].append(
            {"id": item["id"], "availability": item["availability"], "check": state}
        )
        if state == "mismatch":
            return invalid(f"source digest mismatch for {item['id']}", "evidence_mismatch")

    counts: dict[str, int] = {}
    for receipt in document["receipts"]:
        counts[receipt["kind"]] = counts.get(receipt["kind"], 0) + 1
    report["receipt_counts"] = counts
    if limited:
        report["status"] = "valid_with_limits"
        report["diagnostics"].append(
            {
                "code": "indeterminate_evidence",
                "message": "source bytes not supplied for every evidence descriptor",
            }
        )
    return report


def verify_files(
    paths: list[Path], evidence: Mapping[str, bytes] | None = None
) -> list[dict]:
    """Verify files, then check repeated revision IDs and resolvable links."""

    reports = []
    documents = []
    for path in paths:
        try:
            data = path.read_bytes()
        except OSError as exc:
            report = _result("invalid", code="input_error", message=str(exc))
            reports.append({"path": str(path), **report})
            documents.append(None)
            continue
        report = verify_bytes(data, evidence if len(paths) == 1 else None)
        reports.append({"path": str(path), **report})
        documents.append(json.loads(data) if report["status"] != "invalid" else None)

    seen: dict[str, tuple[bytes, int]] = {}
    by_revision = {
        doc["finding"]["revision"]: doc
        for doc in documents
        if doc is not None
    }
    for index, document in enumerate(documents):
        if document is None:
            continue
        finding = document["finding"]
        revision = finding["revision"]
        canonical = rfc8785.dumps(finding)
        if revision in seen and seen[revision][0] != canonical:
            other_index = seen[revision][1]
            for target in (other_index, index):
                reports[target]["status"] = "invalid"
                reports[target]["diagnostics"].append(
                    {
                        "code": "invalid_binding",
                        "message": f"conflicting Finding values for revision {revision}",
                    }
                )
        else:
            seen[revision] = (canonical, index)
        for link in finding.get("links", []):
            target = by_revision.get(link["target_revision"])
            if target is None:
                reports[index]["diagnostics"].append(
                    {
                        "code": "unresolved_link",
                        "message": f"{link['relation']} target not supplied: {link['target_revision']}",
                    }
                )
                if reports[index]["status"] == "valid":
                    reports[index]["status"] = "valid_with_limits"
            elif target["finding"]["id"] != link["target_id"]:
                reports[index]["status"] = "invalid"
                reports[index]["diagnostics"].append(
                    {
                        "code": "invalid_binding",
                        "message": f"{link['relation']} target ID does not match target revision",
                    }
                )
            elif (
                link["relation"] == "revision_of"
                and target["finding"]["created_at"] >= finding["created_at"]
            ):
                reports[index]["status"] = "invalid"
                reports[index]["diagnostics"].append(
                    {
                        "code": "invalid_binding",
                        "message": "revision_of target is not earlier",
                    }
                )
    return reports
