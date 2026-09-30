"""Set up a repository to use AFF without altering existing agent instructions."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from .collection import CollectionError, check_index, write_index


class InitError(ValueError):
    """The project cannot be initialized safely."""


def init_project(project: Path) -> list[str]:
    """Create a Git collection and starter instructions, preserving existing files."""

    if project.is_symlink() or not project.is_dir():
        raise InitError(f"project must be an existing regular directory: {project}")
    collection = project / "aff"
    policy = collection / "policy.md"
    agents = project / "AGENTS.md"
    if policy.is_symlink() or agents.is_symlink():
        raise InitError("policy.md and AGENTS.md cannot be symlinks")
    if policy.exists() and not policy.is_file():
        raise InitError(f"policy path must be a regular file: {policy}")
    if agents.exists() and not agents.is_file():
        raise InitError(f"agent instructions path must be a regular file: {agents}")
    try:
        index = collection / "index.md"
        if index.exists() or index.is_symlink():
            check_index(collection)
        else:
            index = write_index(collection)
        messages = [f"collection: {index}"]
        templates = resources.files("oaff").joinpath("templates")
        for path, template in (
            (policy, "policy.md"),
            (agents, "AGENTS.md"),
        ):
            if path.exists():
                messages.append(f"kept existing: {path}")
                continue
            try:
                with path.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(
                        templates.joinpath(template).read_text(encoding="utf-8")
                    )
            except FileExistsError:
                messages.append(f"kept existing: {path}")
            else:
                messages.append(f"created: {path}")
        if agents.exists() and "kept existing: " + str(agents) in messages:
            messages.append("add a pointer to aff/policy.md in your existing AGENTS.md")
        return messages
    except (CollectionError, OSError, UnicodeError) as exc:
        raise InitError(str(exc)) from exc
