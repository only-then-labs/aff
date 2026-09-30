"""Conservative, one-way views for comparing AFF with other formats."""

from __future__ import annotations

import json
from html import escape
from urllib.parse import urlsplit

from .verify import verify_bytes


def okf_view(package_bytes: bytes) -> tuple[str, dict]:
    """Render an AFF package as an OKF v0.2 Markdown discovery view.

    The view is deliberately lossy. It is not an AFF round trip, a source
    verification, or a destination adoption decision.
    """

    verification = verify_bytes(package_bytes)
    if verification["status"] == "invalid":
        raise ValueError(verification["diagnostics"][0]["message"])
    package = json.loads(package_bytes)
    finding = package["finding"]
    def okf_source(uri: str) -> bool:
        parsed = urlsplit(uri)
        return parsed.scheme in {"https", "http"} and bool(parsed.hostname) and not (
            parsed.username or parsed.password
        )

    projected_sources = [
        {"id": row["id"], "resource": row["source_uri"]}
        for row in finding["evidence"] if okf_source(row["source_uri"])
    ]
    frontmatter = {
        "type": "Finding",
        "title": finding["statement"],
        "status": "draft",
    }
    if projected_sources:
        frontmatter["sources"] = projected_sources
    # JSON is valid YAML 1.2. Emit only ordinary OKF fields: an OKF reader
    # cannot mistake an AFF origin receipt for local `verified` metadata.
    def prose(value: str) -> str:
        return escape(value).replace("\r", " ").replace("\n", " ")

    body = [
        "# Finding", "", prose(finding["statement"]), "", "## Applicability", "",
        prose(finding["applicability"]["description"]), "", "Conditions:",
    ]
    body.extend(f"- {prose(item)}" for item in finding["applicability"]["conditions"])
    if finding["applicability"].get("exclusions"):
        body.extend(["", "Exclusions:"])
        body.extend(f"- {prose(item)}" for item in finding["applicability"]["exclusions"])
    body.extend(["", "## Source availability", ""])
    body.extend(
        f"- `{prose(row['id'])}`: {row['availability']} (producer-declared; source bytes not included)"
        for row in finding["evidence"]
    )
    markdown = "---\n" + json.dumps(frontmatter, ensure_ascii=False, sort_keys=True)
    markdown += "\n---\n\n" + "\n".join(body) + "\n"
    loss = {
        "source_format": "AFF/OAFF 0.1.0",
        "target_format": "OKF 0.2 discovery view",
        "finding_id": finding["id"],
        "revision": finding["revision"],
        "package_digest": package["integrity"]["digest"],
        "package_verification": verification["status"],
        "round_trip": False,
        "local_authority": "none",
        "losses": [
            "AFF immutable revision and package digest have no OKF core identity binding",
            "AFF evidence source digests, locators, and excerpts are not structured OKF sources",
            "AFF applicability conditions and exclusions become body prose",
            "AFF producer identity and created_at are not OKF generated/verified actors",
            "AFF receipts cannot become OKF verified or local authorization",
            "AFF typed revision/dependency links cannot become equivalent OKF links",
        ],
    }
    omitted = [row["id"] for row in finding["evidence"]
               if not okf_source(row["source_uri"])]
    if omitted:
        loss["losses"].append(
            "AFF source URIs not expressible as safe OKF URLs were omitted: "
            + ", ".join(omitted)
        )
    return markdown, loss
