"""Git collection behavior at the public CLI boundary."""

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import rfc8785

from oaff.collection import CollectionError, add_package, check_index, write_index

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


class CollectionTest(unittest.TestCase):
    def test_empty_collection_and_repeatable_cli_add(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "aff"
            self.assertEqual(write_index(root), root / "index.md")
            check_index(root)
            for outcome in ("successful", "failed"):
                source = FIXTURES / f"valid/{outcome}-run-finding-valid.aff"
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "oaff.cli",
                        "collection",
                        "add",
                        str(source),
                        "--root",
                        str(root),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            check_index(root)
            packages = sorted((root / "findings").glob("*.aff"))
            self.assertEqual(len(packages), 2)
            index = (root / "index.md").read_text()
            self.assertIn("discovery only", index)
            self.assertIn("successful", index)
            self.assertIn("failed", index)
            self.assertEqual(index.count("[Package "), 2)
            destination = add_package(
                root, FIXTURES / "valid/failed-run-finding-valid.aff"
            )
            self.assertTrue(destination.exists())
            self.assertEqual(len(list((root / "findings").glob("*.aff"))), 2)
            check_index(root)

    def test_invalid_package_and_conflicting_revision_do_not_enter_collection(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "aff"
            candidate = FIXTURES / "valid/candidate-valid.aff"
            add_package(root, candidate)
            before = (root / "index.md").read_bytes()
            with self.assertRaises(CollectionError):
                add_package(root, FIXTURES / "invalid/tampered-statement.aff")
            changed = json.loads(candidate.read_text())
            changed["finding"]["statement"] = (
                "Different conclusion with the same revision."
            )
            # A second package with a new digest but the same revision cannot enter.
            changed["integrity"]["digest"] = hashlib.sha256(
                rfc8785.dumps(
                    {key: value for key, value in changed.items() if key != "integrity"}
                )
            ).hexdigest()
            conflict = Path(directory) / "conflict.aff"
            conflict.write_text(json.dumps(changed))
            with self.assertRaisesRegex(CollectionError, "conflicting Finding values"):
                add_package(root, conflict)
            self.assertEqual((root / "index.md").read_bytes(), before)
            self.assertEqual(len(list((root / "findings").glob("*.aff"))), 1)

    def test_index_drift_and_untrusted_receipts(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "aff"
            add_package(root, FIXTURES / "valid/admitted-valid.aff")
            index = root / "index.md"
            text = index.read_text()
            self.assertIn("do not authenticate issuers", text)
            self.assertNotIn("locally admitted", text)
            index.write_text(text + "manual change\n")
            with self.assertRaisesRegex(CollectionError, "index is stale"):
                check_index(root)
            write_index(root)
            check_index(root)

    def test_receipt_snapshots_remain_separate_without_current_status(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "aff"
            for name in ("candidate", "admitted", "withdrawn"):
                add_package(root, FIXTURES / f"valid/{name}-valid.aff")
            index = (root / "index.md").read_text()
            self.assertEqual(index.count("[Package "), 3)
            self.assertEqual(index.count("## tag:example.org,2026:oaff/finding/"), 1)
            self.assertNotIn("latest package", index)
            self.assertNotIn("approved for reuse", index)
            check_index(root)

    def test_nested_paths_are_linked_and_symlink_packages_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "aff"
            nested = root / "findings" / "team notes"
            nested.mkdir(parents=True)
            package = nested / "finding copy.aff"
            package.write_bytes((FIXTURES / "valid/candidate-valid.aff").read_bytes())
            write_index(root)
            self.assertIn(
                "findings/team%20notes/finding%20copy.aff",
                (root / "index.md").read_text(),
            )
            link = root / "findings" / "other.aff"
            link.symlink_to(package)
            with self.assertRaisesRegex(CollectionError, "regular file"):
                check_index(root)


if __name__ == "__main__":
    unittest.main()
