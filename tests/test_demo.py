"""The packaged demo is a safe, repeatable outside first-run path."""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from oaff.collection import check_index
from oaff.verify import verify_bytes


class DemoTest(unittest.TestCase):
    def test_demo_creates_two_source_bound_unapproved_findings(self):
        with TemporaryDirectory() as directory:
            project = Path(directory) / "trial"
            result = subprocess.run(
                [sys.executable, "-m", "oaff.cli", "demo", "--output", str(project)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertTrue((project / "aff/policy.md").is_file())
            check_index(project / "aff")
            packages = list((project / "aff/findings").glob("*.aff"))
            self.assertEqual(len(packages), 2)
            for package in packages:
                document = json.loads(package.read_bytes())
                self.assertEqual(document["receipts"], [])
                evidence = document["finding"]["evidence"][0]
                name = evidence["source_uri"].rsplit("/", 1)[-1].removesuffix("-run")
                source = (project / "notes" / f"{name}-run.md").read_bytes()
                self.assertEqual(
                    verify_bytes(package.read_bytes(), {evidence["id"]: source})[
                        "status"
                    ],
                    "valid",
                )
            repeat = subprocess.run(
                [sys.executable, "-m", "oaff.cli", "demo", "--output", str(project)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(repeat.returncode, 1)
            self.assertIn("already exists", repeat.stderr)
            self.assertEqual(len(list((project / "aff/findings").glob("*.aff"))), 2)


if __name__ == "__main__":
    unittest.main()
