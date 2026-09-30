"""Create a synthetic, offline first-run project for AFF exploration."""

from __future__ import annotations

from pathlib import Path

from .capture import CaptureError, capture_source
from .collection import CollectionError, add_package, check_index
from .onboarding import InitError, init_project


class DemoError(ValueError):
    """A demo project could not be created."""


_RUNS = (
    (
        "successful",
        "# Synthetic successful run\nAPI v2 create timed out. The retry used the same idempotency key and returned the original resource.\n",
        "In this synthetic API v2 run, retrying after a timeout with the same idempotency key returned the original resource.",
        "An ambiguous create timeout followed by a retry under API v2.",
        ["API v2", "The retry reused the original idempotency key."],
        ["The retry used a different idempotency key."],
    ),
    (
        "failed",
        "# Synthetic failed run\nAPI v2 create timed out. The retry used a new idempotency key and created a second resource.\n",
        "In this synthetic API v2 run, retrying after a timeout with a new idempotency key created a second resource.",
        "An ambiguous create timeout followed by a retry under API v2.",
        ["API v2", "The retry used a new idempotency key."],
        ["The retry reused the original idempotency key."],
    ),
)


def create_demo(output: Path) -> Path:
    """Write two candidate Findings with exact local source bytes and no authority."""

    if output.is_symlink() or output.exists():
        raise DemoError(f"demo destination already exists: {output}")
    try:
        output.mkdir(parents=True)
        init_project(output)
        notes = output / "notes"
        notes.mkdir()
        for (
            name,
            source_text,
            statement,
            applicability,
            conditions,
            exclusions,
        ) in _RUNS:
            source = notes / f"{name}-run.md"
            source.write_text(source_text, encoding="utf-8")
            package = output / f"{name}.aff"
            capture_source(
                source=source,
                source_uri=f"https://example.org/synthetic/aff-demo/{name}-run",
                output=package,
                statement=statement,
                applicability=applicability,
                conditions=conditions,
                exclusions=exclusions,
                producer_id="tag:example.org,2026:agent/aff-demo",
                producer_kind="agent",
            )
            add_package(output / "aff", package)
            package.unlink()
        check_index(output / "aff")
        (output / "README.md").write_text(
            "# Synthetic AFF demo\n\n"
            "The notes and Findings here are synthetic examples, not conclusions about a real API. "
            "Both packages are unapproved candidates.\n\n"
            "1. Read `aff/index.md`, then inspect both `.aff` packages and their conditions.\n"
            "2. Run `aff verify aff/findings/*.aff` for package checks.\n"
            "3. For a source check, find the relevant evidence ID in a package and run "
            "`aff verify PACKAGE --evidence source-1=notes/NAME-run.md`.\n"
            "4. Read `AGENTS.md` and edit `aff/policy.md` before using AFF in a real repository.\n\n"
            "A passing verifier does not prove truth or grant local admission. "
            "See https://github.com/only-then-labs/aff/blob/main/docs/GOVERNANCE.md.\n",
            encoding="utf-8",
        )
        return output
    except (OSError, CaptureError, CollectionError, InitError) as exc:
        raise DemoError(str(exc)) from exc
