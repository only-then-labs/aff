"""Command-line AFF verifier for the OAFF v0.1 wire format."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .capture import CaptureError, capture_source
from .collection import CollectionError, add_package, check_index, write_index
from .verify import verify_files


def main(argv: list[str] | None = None) -> int:
    command_name = Path(sys.argv[0]).name
    parser = argparse.ArgumentParser(
        prog=command_name if command_name in {"aff", "oaff"} else "oaff"
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    verify = subcommands.add_parser("verify", help="verify one or more OAFF files")
    verify.add_argument("packages", nargs="+", type=Path)
    verify.add_argument(
        "--evidence",
        action="append",
        default=[],
        metavar="ID=PATH",
        help="local source bytes for one evidence ID; only with one package",
    )
    verify.add_argument("--json", action="store_true", help="machine-readable reports")
    capture = subcommands.add_parser(
        "capture", help="create a Finding from a local source and explicit conclusion"
    )
    capture.add_argument("--source", required=True, type=Path)
    capture.add_argument("--source-uri", required=True)
    capture.add_argument("--output", required=True, type=Path)
    capture.add_argument("--statement", required=True)
    capture.add_argument("--applicability", required=True)
    capture.add_argument(
        "--condition", action="append", required=True, dest="conditions"
    )
    capture.add_argument("--exclusion", action="append", default=[], dest="exclusions")
    capture.add_argument("--producer-id", required=True)
    capture.add_argument(
        "--producer-kind",
        required=True,
        choices=("agent", "human", "service", "system"),
    )
    capture.add_argument(
        "--type",
        default="observation",
        choices=("observation", "procedure", "constraint"),
    )
    capture.add_argument(
        "--availability",
        default="restricted",
        choices=("public", "restricted", "unavailable"),
    )
    capture.add_argument("--locator")
    collection = subcommands.add_parser(
        "collection", help="manage a Git-native AFF collection"
    )
    collection_commands = collection.add_subparsers(
        dest="collection_command", required=True
    )
    for name, help_text in (
        ("init", "create an empty aff/ collection and index"),
        ("index", "regenerate the collection index"),
        ("check", "verify packages and check the generated index"),
        ("add", "add a verified package and update the index"),
    ):
        command = collection_commands.add_parser(name, help=help_text)
        if name == "add":
            command.add_argument("package", type=Path)
        command.add_argument("--root", type=Path, default=Path("aff"))
    args = parser.parse_args(argv)

    if args.command == "capture":
        try:
            path = capture_source(
                source=args.source,
                source_uri=args.source_uri,
                output=args.output,
                statement=args.statement,
                applicability=args.applicability,
                conditions=args.conditions,
                exclusions=args.exclusions,
                producer_id=args.producer_id,
                producer_kind=args.producer_kind,
                finding_type=args.type,
                availability=args.availability,
                locator=args.locator,
            )
            print(path)
        except CaptureError as exc:
            print(f"capture error: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.command == "collection":
        try:
            if args.collection_command in {"init", "index"}:
                index = write_index(args.root)
                print(index)
            elif args.collection_command == "check":
                check_index(args.root)
                print(f"valid collection: {args.root}")
            else:
                destination = add_package(args.root, args.package)
                print(destination)
        except (CollectionError, OSError, UnicodeError) as exc:
            print(f"collection error: {exc}", file=sys.stderr)
            return 1
        return 0

    evidence = {}
    if args.evidence and len(args.packages) != 1:
        parser.error("--evidence requires exactly one package")
    for item in args.evidence:
        key, separator, path = item.partition("=")
        if not separator or not key or not path or key in evidence:
            parser.error("--evidence must be a unique ID=PATH pair")
        try:
            evidence[key] = Path(path).read_bytes()
        except OSError as exc:
            parser.error(str(exc))

    reports = verify_files(args.packages, evidence)
    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        for report in reports:
            print(f"{report['status']}: {report['path']}")
            for diagnostic in report["diagnostics"]:
                print(f"  {diagnostic['code']}: {diagnostic['message']}")
    return 1 if any(report["status"] == "invalid" for report in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
