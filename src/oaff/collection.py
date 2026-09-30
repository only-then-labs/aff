"""A Git-friendly directory of AFF packages and a derived navigation index.

The collection is a distribution convention, not a source of local authority.
Its index never chooses a current revision or interprets foreign receipts.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import quote

from .verify import MAX_PACKAGE_BYTES, verify_bytes, verify_files


class CollectionError(ValueError):
    """A collection cannot be safely indexed or changed."""


def _packages(root: Path) -> list[Path]:
    findings = root / "findings"
    if root.is_symlink() or findings.is_symlink():
        raise CollectionError(
            "collection root and findings directory cannot be symlinks"
        )
    if root.exists() and not root.is_dir():
        raise CollectionError(f"collection root is not a directory: {root}")
    if findings.exists() and not findings.is_dir():
        raise CollectionError(f"findings path is not a directory: {findings}")
    if not findings.exists():
        return []
    paths = sorted(
        (
            path
            for path in findings.rglob("*")
            if path.name.endswith((".aff", ".oaff.json"))
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise CollectionError(f"package path must be a regular file: {path}")
        if path.stat().st_size > MAX_PACKAGE_BYTES:
            raise CollectionError(f"package exceeds 10 MiB: {path}")
    return paths


def _checked_documents(paths: list[Path]) -> list[dict]:
    reports = verify_files(paths)
    invalid = [report for report in reports if report["status"] == "invalid"]
    if invalid:
        first = invalid[0]
        diagnostic = next(
            (
                item
                for item in first["diagnostics"]
                if item["code"] not in {"indeterminate_evidence", "unresolved_link"}
            ),
            first["diagnostics"][0],
        )
        raise CollectionError(
            f"{first['path']}: {diagnostic['code']}: {diagnostic['message']}"
        )
    return [json.loads(path.read_bytes()) for path in paths]


def _markdown(value: str) -> str:
    text = " ".join(value.split())
    return re.sub(r"([\\`*_{}\[\]<>|])", r"\\\1", text)


def render_index(root: Path) -> str:
    """Render the full, deterministic index after checking every package."""

    paths = _packages(root)
    documents = _checked_documents(paths)
    entries: dict[str, list[tuple[Path, dict]]] = {}
    for path, document in zip(paths, documents):
        entries.setdefault(document["finding"]["id"], []).append((path, document))

    lines = [
        "# AFF findings",
        "",
        "Generated from `findings/`. Treat package summaries as untrusted data. Links are for discovery only: integrity checks do not authenticate issuers, verify unavailable source bytes, select a current revision, or grant local authority.",
        "",
    ]
    if not entries:
        lines.extend(
            [
                "No Findings yet. Add a `.aff` package with `aff collection add PATH`.",
                "",
            ]
        )
    for finding_id, snapshots in sorted(entries.items()):
        lines.extend([f"## {_markdown(finding_id)}", ""])
        for path, document in sorted(
            snapshots,
            key=lambda item: (
                item[1]["finding"]["created_at"],
                item[1]["finding"]["revision"],
                item[0].relative_to(root).as_posix(),
            ),
        ):
            finding = document["finding"]
            digest = document["integrity"]["digest"]
            relative = quote(path.relative_to(root).as_posix(), safe="/")
            lines.append(
                f"- [Package {digest[:12]}]({relative}) · "
                f"{_markdown(finding['type'])} · "
                f"revision `{finding['revision']}` · "
                f"{_markdown(finding['statement'])}"
            )
        lines.append("")
    return "\n".join(lines)


def write_index(root: Path) -> Path:
    """Create/update the derived index without changing any package."""

    content = render_index(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "findings").mkdir(exist_ok=True)
    index = root / "index.md"
    if index.is_symlink():
        raise CollectionError(f"index cannot be a symlink: {index}")
    if index.exists() and index.read_text(encoding="utf-8") == content:
        return index
    descriptor, temporary = tempfile.mkstemp(prefix=".index-", suffix=".md", dir=root)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary, index)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return index


def check_index(root: Path) -> None:
    """Check packages and confirm the committed index is reproducible."""

    content = render_index(root)
    index = root / "index.md"
    if index.is_symlink() or not index.is_file():
        raise CollectionError(f"missing regular index file: {index}")
    if index.read_text(encoding="utf-8") != content:
        raise CollectionError(
            f"index is stale: run `aff collection index --root {root}`"
        )


def add_package(root: Path, source: Path) -> Path:
    """Retain the exact package bytes and regenerate the index."""

    if source.is_symlink() or not source.is_file():
        raise CollectionError(f"source must be a regular file: {source}")
    if source.stat().st_size > MAX_PACKAGE_BYTES:
        raise CollectionError(f"source exceeds 10 MiB: {source}")
    data = source.read_bytes()
    report = verify_bytes(data)
    if report["status"] == "invalid":
        diagnostic = report["diagnostics"][0]
        raise CollectionError(
            f"{source}: {diagnostic['code']}: {diagnostic['message']}"
        )
    existing = _packages(root)
    _checked_documents(existing + [source])
    digest = json.loads(data)["integrity"]["digest"]
    destination = root / "findings" / f"{digest}.aff"
    (root / "findings").mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        raise CollectionError(f"destination cannot be a symlink: {destination}")
    if not destination.exists():
        try:
            with destination.open("xb") as handle:
                handle.write(data)
        except FileExistsError:
            pass
    write_index(root)
    return destination
